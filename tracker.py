import cv2
import sys
import pandas as pd
import math
import argparse
import os

from plotting import plot_angle, fit_amplitude, binning, amplitude_decay


def _create_tracker(name):
    """Create an OpenCV tracker instance by name."""
    name = name.upper()
    if name == "CSRT":
        try:
            return cv2.legacy.TrackerCSRT_create()
        except AttributeError:
            return cv2.TrackerCSRT_create()
    if name == "KCF":
        try:
            return cv2.legacy.TrackerKCF_create()
        except AttributeError:
            return cv2.TrackerKCF_create()
    if name == "BOOSTING":
        try:
            return cv2.legacy.TrackerBoosting_create()
        except AttributeError:
            return cv2.TrackerBoosting_create()
    if name == "MIL":
        try:
            return cv2.legacy.TrackerMIL_create()
        except AttributeError:
            return cv2.TrackerMIL_create()
    if name == "TLD":
        try:
            return cv2.legacy.TrackerTLD_create()
        except AttributeError:
            return cv2.TrackerTLD_create()
    if name == "MEDIANFLOW":
        try:
            return cv2.legacy.TrackerMedianFlow_create()
        except AttributeError:
            return cv2.TrackerMedianFlow_create()
    if name == "MOSSE":
        try:
            return cv2.legacy.TrackerMOSSE_create()
        except AttributeError:
            return cv2.TrackerMOSSE_create()
    raise ValueError(f"Unknown tracker name: {name}")


def process_video(tracker, video_path, csv_path, ret=False, hilo_length_cm=30, area_condition="sin_hojas"):
    """
    Process a video to track an object and log its position and angle over time.
    Args:
        tracker (cv2.Tracker): The OpenCV tracker object to use for tracking.
        video_path (str): Path to the input video file.
        csv_path (str): Path to save the CSV file containing the tracking results.
        ret (bool, optional): If True, returns tracking results. Defaults False.
        hilo_length_cm (float): Length of the string in cm. Default is 30.
        area_condition (str): Experimental condition - "sin_hojas" or "con_hojas". Default is "sin_hojas".
    Returns:
        tuple: If ret is True, returns a tuple containing fitted amplitude data, total time, and q_factor.
    Notes:
    - The user is required to manually select an equilibrium point and ROI in the first frame.
    - The function logs the position and angle of the tracked object at regular intervals.
    - Angle is calculated using θ = arcsin((x_c - x_0) / L_px) where L_px is the string length in pixels.
    - Results are saved to CSV, and an amplitude plot is generated.
    """

    video = cv2.VideoCapture(video_path)

    # Exit if video not opened.
    if not video.isOpened():
        print("Could not open video")
        sys.exit()

    # Get video properties
    recorded_fps = video.get(cv2.CAP_PROP_FPS)
    frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Before starting the tracking, let the user pick a equilibrium point as origin
    origin = None

    def select_point(event, x, y, flags, param):
        nonlocal origin
        if event == cv2.EVENT_LBUTTONDOWN:
            origin = (x, y)
            print(f"Equilibrium Point set at: X = {x}, Y = {y}")

    ok, frame = video.read()
    if not ok:
        print('Cannot read video file')
        sys.exit()

    cv2.namedWindow("Select Equilibrium Point", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select Equilibrium Point", min(frame_width, 800), min(frame_height, 600))
    cv2.setMouseCallback("Select Equilibrium Point", select_point)

    while origin is None:
        cv2.imshow("Select Equilibrium Point", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit()

    cv2.destroyWindow("Select Equilibrium Point")

    # Let the user select the ROI (bounding box) manually on the first frame
    cv2.namedWindow("Select Object", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select Object", min(frame_width, 800), min(frame_height, 600))
    bounding_box = cv2.selectROI("Select Object", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()

    # Calculate L_px (string length in pixels) from first frame
    # L_px is the vertical distance from origin (support point) to initial position of mass
    x_bb, y_bb, w_bb, h_bb = map(int, bounding_box)
    mass_y_initial = y_bb + h_bb // 2
    L_px = abs(origin[1] - mass_y_initial)  # Vertical distance is the string length
    
    if L_px < 10:
        print("Warning: L_px is very small. Ensure ROI was selected correctly.")
        L_px = 100  # Default fallback

    # Initialize tracker with first frame and bounding box
    if isinstance(tracker, str):
        cvtracker = _create_tracker(tracker)
    elif hasattr(tracker, 'init') and hasattr(tracker, 'update'):
        cvtracker = tracker
    else:
        raise TypeError("tracker must be a tracker object or a tracker name string")

    ok = cvtracker.init(frame, bounding_box)

    position_log = []
    current_frame = 0

    # Normalize angle helper
    def normalize_angle(a):
        # Map angles to [-90, 90] range for consistency
        while a > 90:
            a -= 180
        while a < -90:
            a += 180
        return a

    adj_x, adj_y, angle = 0, 0, 0

    while True:
        ok, frame = video.read()
        if not ok:
            break

        ok, bbox = cvtracker.update(frame)
        current_time = (current_frame / recorded_fps)

        if ok:
            x, y, w, h = map(int, bbox)
            p1 = (x, y)
            p2 = (x + w, y + h)
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)

            center_x = x + w // 2
            center_y = y + h // 2

            # Calculate displacement from equilibrium point
            adj_x = center_x - origin[0]
            adj_y = origin[1] - center_y  # CORRECTED: use origin[1] for y coordinate

            # Convert pixel displacement to angle using θ = arcsin(x_c / L_px)
            # With small angle approximation: θ ≈ x_c / L_px
            if L_px > 0:
                angle_rad = math.asin(adj_x / L_px) if abs(adj_x / L_px) <= 1 else 0
                angle = math.degrees(angle_rad)
                angle = normalize_angle(angle)
            else:
                angle = 0

            if current_frame % 5 == 0:
                position_log.append([round(current_time, 3), adj_x, adj_y, round(angle, 3)])

            # Display information on screen
            cv2.putText(frame, f"Time: {current_time:.2f}s, X: {adj_x:.2f}px, Y:{adj_y:.2f}px", 
                       (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 170, 50), 2)
            cv2.putText(frame, f"Angle: {angle:.2f}°, L_px: {L_px}", 
                       (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 170, 50), 2)

        else:
            cv2.putText(frame, "Tracking failure detected", (100, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)

        # Display result
        cv2.namedWindow("Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Tracking", min(frame_width, 800), min(frame_height, 600))
        cv2.imshow("Tracking", frame)

        # Exit if ESC pressed
        k = cv2.waitKey(1) & 0xff
        if k == 27:
            break

        current_frame += 1

    # Release resources
    video.release()
    cv2.destroyAllWindows()

    # Save data to CSV
    df = pd.DataFrame(position_log, columns=["Time(s)", "X", "Y", "Angle(deg)"])
    df.to_csv(csv_path, index=False)
    print(f"Position data saved to {csv_path}")

    # Generate plots and extract fit results
    png_path = os.path.splitext(csv_path)[0] + '.png'
    metadata_path = os.path.splitext(csv_path)[0] + '_metadata.csv'
    
    if ret:
        data_dict, q_factor = fit_amplitude(df, output_path=png_path, ret=True, 
                                           hilo_length_cm=hilo_length_cm,
                                           area_condition=area_condition,
                                           metadata_output_path=metadata_path)
    else:
        fit_amplitude(df, output_path=png_path, 
                     hilo_length_cm=hilo_length_cm,
                     area_condition=area_condition,
                     metadata_output_path=metadata_path)
    
    print(f"Amplitude plot saved to {png_path}")
    print(f"Metadata saved to {metadata_path}")

    if ret:
        return data_dict, df["Time(s)"].iloc[-1], q_factor

def process_directory(tracker, directory, ret=False, experiment_config=None):
    """
    Processes all video files in a given directory using a specified tracker.
    Args:
        tracker: The tracking object or function used to process the videos.
        directory (str): The path to the directory containing video files.
        ret (bool, optional): If True, returns additional data for further processing. Defaults to False.
        experiment_config (dict, optional): Configuration dict with experiment metadata.
            Expected keys: 
            - 'hilo_length_cm': float (default 30)
            - 'area_condition': str 'sin_hojas' or 'con_hojas' (default 'sin_hojas')
            - 'experiment_id': int 1-4 for 2^2 factorial design (optional)
    Returns:
        None or tuple: If `ret` is True, returns a tuple containing:
            - times (list): List of time bins.
            - means (list): List of mean values for each bin.
            - uncertainties (list): List of uncertainties for each bin.
        Otherwise, returns None.
    Raises:
        FileNotFoundError: If the specified directory does not exist.
        Exception: If an error occurs during video processing.
    Notes:
        - Supported video file formats are: .mov, .MOV, .mp4, .avi, .mkv.
        - Processed video data is saved in the ./output directory with a corresponding CSV file.
    Example:
        process_directory(my_tracker, "/path/to/videos", ret=True)
    """
    
    if experiment_config is None:
        experiment_config = {
            'hilo_length_cm': 30,
            'area_condition': 'sin_hojas',
            'experiment_id': 0
        }
    
    hilo_length = experiment_config.get('hilo_length_cm', 30)
    area_condition = experiment_config.get('area_condition', 'sin_hojas')

    # Get a list of all files in the directory
    video_files = [f for f in os.listdir(directory) if f.endswith(('.mov', '.MOV', '.mp4', '.avi', '.mkv'))]

    if ret:
        trials = []
        length = []
        q_facotrs = []

    if not video_files:
        print("No video files found in the directory.")
        return

    # Loop through each video file and process it
    for video_file in video_files:
        video_path = os.path.join(directory, video_file)

        # By default all output are in ./output
        output_csv_path = os.path.join("./output", f"{os.path.splitext(video_file)[0]}_output.csv")

        # Call the video processing function
        if ret:
            data, time, q_factor = process_video(tracker, video_path, output_csv_path, ret=True,
                                                hilo_length_cm=hilo_length,
                                                area_condition=area_condition)
            trials.append(data)
            length.append(time)
            q_facotrs.append(q_factor)
        else:
            process_video(tracker, video_path, output_csv_path,
                         hilo_length_cm=hilo_length,
                         area_condition=area_condition)

    if ret:
        times, means, uncertainties = binning(trials, max_time=max(length))
        average_q = sum(q_facotrs) / len(q_facotrs) if len(q_facotrs) >= 0 else 0
        amplitude_decay(times, means, uncertainties, average_q, output_path=f"./output/decay_fit_{directory}.png")

    print(f"Processed {len(video_files)} video files in directory: {directory}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Specify tracker and source directory.")

    parser.add_argument(
        '--tracker',
        type=str,
        help='Please use capitalized name, see README.md',
        default="KCF"
    )

    parser.add_argument(
        '--source',
        type=str,
        default="videos",
        help='Source directory path as string.'
    )

    parser.add_argument(
        '--multi-trials', '-m',
        type=str,
        default="False",
        help='Run multiple trials to get mean and error'
    )

    args = parser.parse_args()

    if not os.path.isdir(args.source):
        raise NotADirectoryError(f"'{args.source}' is not a valid directory.")

    ret = True if args.multi_trials == "True" else False

    print(f"Using tracker: {args.tracker}")
    print(f"Operating on source directory: {args.source}")

    # CURRENTLY we manually set return as true or false!
    process_directory(args.tracker, args.source, ret)