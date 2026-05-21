import cv2
from plotting import fit_amplitude
from detection import detect_object
import sys, pandas as pd, math, argparse, os
from scipy.signal import savgol_filter
from datetime import datetime

def live_track(tracker, video_src, hilo_length_cm=30, area_condition="sin_hojas", output_dir="./tracking_output"):
    """
    Live track pendulum using webcam or video file.
    
    Args:
        tracker: OpenCV tracker object
        video_src: Video source (0 for webcam, or path to video file)
        hilo_length_cm: Length of the string in cm. Default is 30.
        area_condition: Experimental condition - "sin_hojas" or "con_hojas". Default is "sin_hojas".
        output_dir: Directory to save output files. Default is "./tracking_output"
    
    Returns:
        tuple: (position_log dataframe, L_px, origin)
    """

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    roi = detect_object()

    cap = cv2.VideoCapture(int(video_src) if isinstance(video_src, str) and video_src.isdigit() else video_src)

    # Exit if video not opened.
    if not cap.isOpened():
        print("Could not open video")
        sys.exit()

    # Before starting the tracking, let the user pick a equilibrium point as origin
    origin = None

    def select_point(event, x, y, flags, param):
        nonlocal origin
        if event == cv2.EVENT_LBUTTONDOWN:
            origin = (x, y)
            print(f"Equilibrium Point set at: X = {x}, Y = {y}")

    ret, frame = cap.read()
    if not ret:
        print('Cannot read video file')
        sys.exit()

    # Limit window size, resize frame if necessary
    frame_height, frame_width = frame.shape[:2]
    cv2.namedWindow("Select Equilibrium Point", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select Equilibrium Point", min(frame_width, 800), min(frame_height, 600))

    cv2.setMouseCallback("Select Equilibrium Point", select_point)

    print("\n📍 Click on the equilibrium point (support/pivot point)")
    while origin is None:
        cv2.imshow("Select Equilibrium Point", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit() 

    cv2.destroyWindow("Select Equilibrium Point")

    # Calculate L_px (string length in pixels) from ROI
    x_roi, y_roi, w_roi, h_roi = map(int, roi)
    mass_y_initial = y_roi + h_roi // 2
    L_px = abs(origin[1] - mass_y_initial)  # Vertical distance is the string length
    
    if L_px < 10:
        print("Warning: L_px is very small. Ensure ROI was selected correctly.")
        L_px = 100  # Default fallback
    
    print(f"✓ String length in pixels (L_px): {L_px} px")

    # Initialize tracker with first frame and bounding box
    ok = tracker.init(frame, roi)

    position_log = []
    current_frame = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\n▶️  Starting live tracking (Press 'q' to stop)...")
    print(f"   FPS: {fps:.2f}")
    print(f"   ROI: {roi}")
    print("-" * 70)

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        ok, bbox = tracker.update(frame)
        current_time = (current_frame / fps) if fps > 0 else current_frame / 30.0
        
        if ok:
            x, y, w, h = map(int, bbox)
            p1 = (x, y)
            p2 = (x + w, y + h)
            cv2.rectangle(frame, p1, p2, (0, 255, 0), 2, 1)
            
            # Draw equilibrium point
            cv2.circle(frame, origin, 5, (0, 0, 255), -1)

            center_x = x + w // 2
            center_y = y + h // 2

            # Calculate displacement from equilibrium point
            adj_x = center_x - origin[0]
            adj_y = origin[1] - center_y  # CORRECTED: use origin[1] for y coordinate

            # Convert pixel displacement to angle using θ = arcsin(x_c / L_px)
            if L_px > 0:
                angle_rad = math.asin(adj_x / L_px) if abs(adj_x / L_px) <= 1 else 0
                angle = math.degrees(angle_rad)
            else:
                angle = 0
            
            if current_frame % 5 == 0:
                position_log.append([round(current_time, 3), adj_x, adj_y, round(angle, 3)])

            # Display information on screen
            cv2.putText(frame, f"Time: {current_time:.2f}s | X: {adj_x:.1f}px | Y: {adj_y:.1f}px", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Angle: {angle:.2f}° | L_px: {L_px} px | FPS: {fps:.1f}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to stop tracking", 
                       (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        else:
            cv2.putText(frame, "Tracking failure detected", (100, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
            
        # Display result
        cv2.namedWindow("Live Tracking", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Live Tracking", min(frame_width, 1000), min(frame_height, 700))
        cv2.imshow("Live Tracking", frame)

        # Exit if 'q' pressed
        k = cv2.waitKey(1) & 0xff
        if k == ord('q'):
            print("\n🛑 Stopping tracking...")
            break

        current_frame += 1

    # Release resources
    cap.release()
    cv2.destroyAllWindows()

    if not position_log:
        print("✗ No data captured during tracking")
        return None, L_px, origin

    # Save data to CSV
    df = pd.DataFrame(position_log, columns=["Time(s)", "X", "Y", "Angle(deg)"])
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save tracking data
    csv_path = os.path.join(output_dir, f"live_track_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n✓ Position data saved to: {csv_path}")
    print(f"  Total frames: {len(df)}")
    print(f"  Duration: {df['Time(s)'].iloc[-1]:.2f}s")
    print(f"  Angle range: [{df['Angle(deg)'].min():.2f}°, {df['Angle(deg)'].max():.2f}°]")

    # Generate plot with fit_amplitude
    png_path = os.path.join(output_dir, f"live_track_amplitude_{timestamp}.png")
    metadata_path = os.path.join(output_dir, f"live_track_metadata_{timestamp}.csv")
    
    try:
        fit_amplitude(df, output_path=png_path, 
                     hilo_length_cm=hilo_length_cm,
                     area_condition=area_condition,
                     metadata_output_path=metadata_path)
        print(f"✓ Amplitude plot saved to: {png_path}")
        print(f"✓ Metadata saved to: {metadata_path}")
    except Exception as e:
        print(f"⚠ Could not generate amplitude plot: {e}")
    
    return df, L_px, origin
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live pendulum tracking with real-time data capture.")

    parser.add_argument(
        '--tracker',
        type=str,
        help='Tracker type (KCF, CSRT, MOSSE)',
        default="KCF",
        choices=["KCF", "CSRT", "MOSSE"]
    )

    parser.add_argument(
        '--source',
        type=str,
        default="0",
        help='Video source (0 for webcam, or path to video file)'
    )
    
    parser.add_argument(
        '--hilo-length',
        type=float,
        default=30.0,
        help='Length of the pendulum string in cm (default: 30)'
    )
    
    parser.add_argument(
        '--area-condition',
        type=str,
        default="sin_hojas",
        choices=["sin_hojas", "con_hojas"],
        help='Experimental area condition'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default="./tracking_output",
        help='Directory to save output files'
    )

    args = parser.parse_args()

    # Create tracker
    if args.tracker == "KCF":
        tracker = cv2.TrackerKCF_create()
    elif args.tracker == "CSRT":
        tracker = cv2.legacy.TrackerCSRT_create()
    elif args.tracker == "MOSSE":
        tracker = cv2.legacy.TrackerMOSSE_create()
    else:
        tracker = cv2.TrackerKCF_create()

    print("=" * 70)
    print("LIVE PENDULUM TRACKING - REAL DATA CAPTURE")
    print("=" * 70)
    print(f"✓ Tracker: {args.tracker}")
    print(f"✓ Video source: {args.source}")
    print(f"✓ Hilo length: {args.hilo_length} cm")
    print(f"✓ Area condition: {args.area_condition}")
    print(f"✓ Output directory: {args.output_dir}")
    print("=" * 70)

    try:
        live_track(tracker, args.source, 
                  hilo_length_cm=args.hilo_length,
                  area_condition=args.area_condition,
                  output_dir=args.output_dir)
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)