import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit
import argparse
import math, os, glob
import warnings

def binning(trials, max_time, bin_size=1):
    """
    Bins the amplitude data from multiple trials into specified time bins and calculates the mean and uncertainty of the mean for each bin.
    Args:
        trials (list of list of tuples): A list where each element is a trial, and each trial is a list of (timestamp, amplitude) tuples.
        max_time (float): The maximum time up to which the data should be binned.
        bin_size (float, optional): The size of each time bin. Default is 1.
    Returns:
        tuple: A tuple containing:
            - bin_centers (numpy.ndarray): The centers of the time bins.
            - mean_amplitudes (numpy.ndarray): The mean amplitude for each time bin.
            - uncertainty_mean (list): The uncertainty of the mean amplitude for each time bin.
    """

    bins = np.arange(0, max_time + bin_size, bin_size)

    # Initialize lists to hold max amplitudes per trial
    max_amplitudes_per_trial = []

    # Find max amplitude for each trial
    for trial in trials:
        max_amplitude = []
        for timestamp, amplitude in trial:
            max_amplitude.append(amplitude)
        max_amplitudes_per_trial.append(max(max_amplitude))

    # Now bin the max amplitudes
    mean_amplitudes = []
    std_amplitudes = []

    for start in bins[:-1]:
        bin_amplitudes = []
        for trial in trials:
            for timestamp, amplitude in trial:
                if start <= timestamp < start + bin_size:
                    bin_amplitudes.append(amplitude)

        if bin_amplitudes:
            mean_amplitudes.append(np.mean(bin_amplitudes))
            std_amplitudes.append(np.std(bin_amplitudes))
        else:
            mean_amplitudes.append(np.nan)
            std_amplitudes.append(np.nan)

    # Convert to numpy arrays for further use or plotting
    mean_amplitudes = np.array(mean_amplitudes)
    std_amplitudes = np.array(std_amplitudes)
    
    # Calculate uncertainty of the mean
    uncertainty_mean = [std / np.sqrt(len(trials)) if len(trials) > 0 else np.nan for std in std_amplitudes]
    
    # Create a mask that identifies positions where both arrays are not NaN
    valid_mask = ~np.isnan(mean_amplitudes) & ~np.isnan(uncertainty_mean)

    # Apply the mask to filter out the NaN values from both arrays
    mean_amplitudes = mean_amplitudes[valid_mask]
    uncertainty_mean = uncertainty_mean[valid_mask]

    # Calculate bin centers for plotting
    bin_centers = bins[:-1] + bin_size / 2
    bin_centers = bin_centers[valid_mask]

    return bin_centers, mean_amplitudes, uncertainty_mean


def calculate_periods(peaks, times):
        """
        Calculate the average period between peaks in a time series.
        Args:
            peaks (list of int): Indices of the peaks in the time series.
            times (list of float): Time values corresponding to each index in the time series.
        Returns:
            float: The average period between consecutive peaks. Returns 0 if no periods are recorded.
        """

        periods = []
        for i in range(1, len(peaks)):
            period = times[peaks[i]] - times[peaks[i - 1]]
            periods.append(period)
        
        try:
            average_period = sum(periods) / len(periods)
            return average_period
        except ZeroDivisionError:
            print("No period recorded, error plotting")
            return 0


def plot_angle(df, output_path="angle_graph.png"):
    """
    Plots the angle of a pendulum over time and saves the plot as an image.
    Args:
        df (pandas.DataFrame): DataFrame containing the pendulum data with columns "Angle(deg)" and "Time(s)".
        output_path (str): The file path where the plot image will be saved. Default is "angle_graph.png".
    Returns:
        None
    The function performs the following steps:
    1. Extracts the angle and time data from the DataFrame.
    2. Finds the peaks (maxima) in the angle data.
    3. Calculates the average period of the pendulum.
    4. Plots the angle vs. time graph.
    5. Adds a title, labels, and grid to the plot.
    6. Saves the plot as a PNG image to the specified output path.
    7. Displays the plot.
    """

    angles = df["Angle(deg)"].values
    times = df["Time(s)"].values

    # Find peaks (maxima) in the angle data
    peaks, _ = find_peaks(angles)

    # Calculate periods

    average_period = calculate_periods(peaks, times)

    # Plot Angle vs Time
    plt.figure(figsize=(10, 6))
    plt.plot(df["Time(s)"], df["Angle(deg)"], marker='o', linestyle='-', color='b')
    plt.title("Pendulum Angle vs Time")
    plt.suptitle(f"Average Period: {average_period:.4f} seconds")
    plt.xlabel("Time (s)")
    plt.ylabel("Angle (degrees)")
    plt.grid(True)
    plt.savefig(f"{output_path}", format="png")
    plt.show()


def q_factor_counting(peak_times, peak_amplitudes, period):
    """
    Calculate the Q factor of a signal based on its peak times and amplitudes.
    Parameters:
        peak_times (pd.Series): Series of peak times.
        peak_amplitudes (pd.Series): Series of peak amplitudes.
        period (float): Period of the signal.
    Returns:
        float: The calculated Q factor.
    """

    # Calculate the threshold amplitude (e^(-π/4) of the initial peak amplitude)
    max_amplitude = peak_amplitudes.iloc[0]
    decay_threshold = max_amplitude * np.exp(-np.pi / 8)

    # Find the time where the amplitude falls below the decay threshold
    decay_time = None
    for i, amplitude in enumerate(peak_amplitudes):
        if amplitude <= decay_threshold:
            decay_time = peak_times.iloc[i]
            break

    if decay_time is None:
        print("WARNING: Amplitude never decays to the required threshold.")
        return -1

    # Calculate the time difference from the initial peak
    initial_time = peak_times.iloc[0]
    decay_duration = decay_time - initial_time

    # Find Q/8 and calculate Q 
    q_factor = i * 8

    return q_factor, decay_duration


def fit_amplitude(df, ret=False, err=None, output_path="amplitude_decay.png", fit_type="e", 
                  hilo_length_cm=30, area_condition="sin_hojas", metadata_output_path=None):
    """
    Fits the amplitude of a damped oscillator to an exponential decay function and plots the results.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing the columns "Angle(deg)" and "Time(s)".
    ret (bool, optional): If True, returns amplitude data and fit results. Default is False.
    err (numpy.ndarray, optional): Error bars for peak amplitudes. Default is None.
    output_path (str, optional): Path to save the plot. Default is "amplitude_decay.png".
    fit_type (str, optional): Type of fit - "e" for exponential, "l" for linear. Default is "e".
    hilo_length_cm (float): Length of the string in cm. Default is 30.
    area_condition (str): Experimental condition - "sin_hojas" or "con_hojas". Default is "sin_hojas".
    metadata_output_path (str, optional): Path to save metadata to CSV. Default is None.
    
    Returns:
    tuple: If ret is True, returns (fit_results_dict, q_factor).
    
    Notes:
    - Applies Savitzky-Golay filter for smoothing.
    - Extracts peaks using scipy.signal.find_peaks.
    - Calculates β (beta, damping factor) and its uncertainty σβ.
    - Exports results to CSV with metadata if metadata_output_path is provided.
    """
    angles = df["Angle(deg)"].values
    angles_rad = np.radians(angles)
    times = df["Time(s)"].values
    
    # Calculate adaptive window for Savitzky-Golay filter
    fps = len(times) / (times[-1] - times[0]) if len(times) > 1 else 30
    period_estimate = 2 * np.pi / np.sqrt(9.7772 / (hilo_length_cm / 100))  # Theoretical period
    window_size = int(fps * period_estimate / 2)
    if window_size % 2 == 0:
        window_size += 1
    window_size = max(window_size, 5)  # Ensure minimum window
    
    # Apply Savitzky-Golay smoothing
    angles_smoothed = savgol_filter(angles_rad, window_length=min(window_size, len(angles_rad)), 
                                     polyorder=3, mode='nearest')
    
    # Extract peaks from both positive and negative extremes
    peaks_pos, _ = find_peaks(angles_smoothed)
    peaks_neg, _ = find_peaks(-angles_smoothed)
    peaks = np.sort(np.concatenate([peaks_pos, peaks_neg]))
    
    peak_times = times[peaks]
    peak_amplitudes = np.abs(angles_smoothed[peaks])  # Take absolute value for envelope
    
    # Generate error bars for peak amplitudes
    error = np.radians(0.03 * np.ones_like(peak_times)) if err is None else err
    xerr = 0.0083 * np.ones_like(peak_times)
    
    beta_value = None
    sigma_beta = None
    q_factor = None
    tau = None
    average_period = None

    if fit_type == 'e':
        # Fit the peak heights to an exponential function A * exp(-beta * t)
        def exponential_decay(t, A, beta):
            return A * np.exp(-beta * t)

        try:
            # Perform curve fitting with covariance for uncertainty estimation
            popt, pcov = curve_fit(exponential_decay, peak_times, peak_amplitudes, 
                                   p0=[peak_amplitudes[0], 0.01], maxfev=5000)
            
            fitted_A, beta_value = popt
            
            # Calculate uncertainty in beta from covariance matrix
            sigma_beta = np.sqrt(np.diag(pcov)[1]) if len(popt) > 1 else 0
            
            # Generate the fitted curve
            fitted_peak_heights = exponential_decay(peak_times, fitted_A, beta_value)
            residual = peak_amplitudes - fitted_peak_heights
            
            # Calculate Q factor and tau
            tau = 1 / beta_value if beta_value > 0 else np.inf
            average_period = calculate_periods(peaks, times)
            q_factor = math.pi * tau / average_period if average_period > 0 else 0
            
        except Exception as e:
            print(f"Curve fitting failed: {e}")
            beta_value = np.nan
            sigma_beta = np.nan
            q_factor = np.nan
            tau = np.nan
            fitted_peak_heights = peak_amplitudes
            residual = np.zeros_like(peak_amplitudes)
   
    elif fit_type == 'l':
        def linear(t, m, b):
            return m*t + b

        popt, pcov = curve_fit(linear, peak_times, peak_amplitudes)

        fitted_m, fitted_b = popt
        beta_value = fitted_m  # Slope represents decay rate in linear model
        sigma_beta = np.sqrt(np.diag(pcov)[0])
        
        fitted_peak_heights = linear(peak_times, fitted_m, fitted_b)
        residual = peak_amplitudes - fitted_peak_heights
        
        average_period = calculate_periods(peaks, times) 

    # Create a figure and two subplots for the top and bottom graphs
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

    # Plot the first graph: Amplitude vs Time
    ax1.errorbar(peak_times, peak_amplitudes, fmt='ro', yerr=error, xerr=xerr, label='Peaks', markersize=3)
    if fit_type=="e" and beta_value is not None and not np.isnan(beta_value):
        ax1.plot(peak_times, fitted_peak_heights, 'g--', 
                label=f'Fitted: {fitted_A:.3f}*exp(-{beta_value:.5f}*t)', markersize=3)
    elif fit_type=='l' and beta_value is not None and not np.isnan(beta_value):
        ax1.plot(peak_times, fitted_peak_heights, 'g--', 
                label=f'Fitted: {fitted_m:.3f}*t + {fitted_b:.3f}', markersize=3)
    
    ax1.set_title("Amplitude vs Time (Smoothed with Savitzky-Golay)")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude (radians)")
    ax1.grid(True)
    ax1.legend()

    # Plot the second graph: Residuals
    ax2.errorbar(peak_times, residual, yerr=error, xerr=xerr, fmt='o', label='Residuals', markersize=3)
    ax2.axhline(0, color='gray', linestyle='--')

    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Residuals')
    if fit_type == 'e':
        ax2.set_title('Residuals of the Exponential Fit')
    elif fit_type == 'l':
        ax2.set_title('Residuals of the Linear Fit')
    ax2.grid(True)
    ax2.legend()

    # Add a text box in the upper-right corner to display Q factor, Tau, and Period
    if q_factor is not None and tau is not None and average_period is not None:
        textstr = (f'β: {beta_value:.5f} ± {sigma_beta:.5f} s⁻¹\n'
                f'Q Factor: {q_factor:.2f}\n'
                f'τ (Tau): {tau:.3f} s\n'
                f'Period: {average_period:.3f} s')
    else:
        textstr = 'Fit failed'
        
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax2.text(0.95, 0.95, textstr, transform=ax2.transAxes, fontsize=10,
            verticalalignment='top', horizontalalignment='right', bbox=props)

    plt.tight_layout(pad=2.0)
    plt.savefig(f"{output_path}", format="png")
    plt.show()

    # Export metadata and results to CSV if requested
    if metadata_output_path is not None:
        results_dict = {
            'Hilo_Length_cm': [hilo_length_cm],
            'Area_Condition': [area_condition],
            'Beta_s-1': [beta_value],
            'Sigma_Beta_s-1': [sigma_beta],
            'Q_Factor': [q_factor],
            'Tau_s': [tau],
            'Period_s': [average_period],
            'Fit_Type': [fit_type]
        }
        results_df = pd.DataFrame(results_dict)
        results_df.to_csv(metadata_output_path, index=False)
        print(f"Metadata saved to {metadata_output_path}")

    if ret:
        return {
            'peak_times': peak_times,
            'peak_amplitudes': peak_amplitudes,
            'beta': beta_value,
            'sigma_beta': sigma_beta,
            'q_factor': q_factor,
            'tau': tau,
            'period': average_period
        }, q_factor
    
def amplitude_decay(times, peaks, error, q_factor, output_path="decay_fit.png"):
    """
    Plots the amplitude decay of a signal over time and fits an exponential decay curve to the data.
    Parameters:
        times (array-like): Array of time values.
        peaks (array-like): Array of peak amplitude values corresponding to the time values.
        error (array-like): Array of error values for the peak amplitudes.
        output_path (str, optional): Path to save the output plot image. Default is "amplitude_decay_trials.png".
    Returns:
        None
    The function performs the following steps:
        1. Defines an exponential decay function.
        2. Fits the exponential decay function to the provided peak data.
        3. Calculates the residuals between the actual peaks and the fitted curve.
        4. Plots the original peak data with error bars and the fitted exponential decay curve.
        5. Plots the residuals of the fit.
        6. Saves the plot to the specified output path and displays it.
    """

    warnings.warn("This function is deprecated and will be removed in future versions.", DeprecationWarning)

    def exponential_decay(t, A, gamma):
        return A * np.exp(-gamma * t)

    # Perform curve fitting to the peak data
    popt, _ = curve_fit(exponential_decay, times, peaks)

    xerr = 0.0083 * np.ones_like(times)

    # Fitted parameters
    fitted_A, fitted_gamma = popt

    # Generate the fitted curve
    fitted_peak_heights = exponential_decay(times, fitted_A, fitted_gamma)
    
    residual = peaks - fitted_peak_heights
    
    plt.figure(figsize=(10, 6))  # Decrease figure height for shorter plots

    plt.subplot(2, 1, 1)
    plt.errorbar(times, peaks, fmt='ro', yerr=error, label='Peaks')
    plt.plot(times, fitted_peak_heights, 'g--', label=f'Fitted: {fitted_A:.3f}*exp(-{fitted_gamma:.3f}*t)')
    plt.suptitle(f"Average Q factor: {q_factor:.3f}")
    plt.title("Amplitude vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (radians)")
    plt.grid(True)
    plt.legend()

    plt.subplot(2, 1, 2)
    # Plot the residuals
    plt.errorbar(times, residual, yerr=error, xerr=xerr, fmt='o', label='Residuals')
    plt.axhline(0, color='gray', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Residuals')
    plt.title('Residuals of the Exponential Fit')
    plt.legend()

    plt.tight_layout(pad=2.0)  # Add padding between plots
    plt.savefig(f"{output_path}", format="png")
    plt.show() 

    print(f"Amplitude decay fit plot saved to {output_path}")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Plot pendulum angle from CSV data.") 
    parser.add_argument("--csv_files_path", nargs="*",help="list of csv files to process.")
    parser.add_argument("--csv_files_directory", type=str, help=" directory containing al csv files containing data.")
    args = parser.parse_args()
    csv_files=[]
    if args.csv_files_path:
        csv_files.extend(args.csv_files_path)
    if args.csv_files_directory:
        csv_files.extend(glob.glob(os.path.join(args.csv_files_directory,"*.csv")))
    if not csv_files:
        print("no csv files provided, please provide them")
    else:
        for i in csv_files:
            try:
                df=pd.read_csv(i,header=0)
                print(f"processing csv file: {i}")
                #functions to run on each csv file
                fit_amplitude(df,output_path=f"output/{os.path.splitext(os.path.basename(i))[0]}_amplitude_decay.png")
                # fit_amplitude(df,output_path=f"output/{os.path.splitext(os.path.basename(i))[0]}_amplitude_decay.png", fit_type="l")
                # plot_angle(df,output_path=f"output/{os.path.splitext(os.path.basename(i))[0]}_angle_graph.png")
            except Exception as e:
                print(f"failed processing {i}: {e}")