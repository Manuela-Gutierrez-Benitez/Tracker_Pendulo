# Pendulum Tracking System - User Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python test_integration.py --mode validate
```

## Live Tracking Modes

### Mode 1: Live Webcam Tracking
Capture real-time pendulum data directly from your webcam:

```bash
# Basic usage (Experiment 1, default settings)
python test_integration.py --mode live --experiment 1

# With custom settings
python test_integration.py --mode live \
  --experiment 1 \
  --output-dir ./my_results
```

**Steps:**
1. A window opens showing your webcam
2. **Click** on the equilibrium point (pivot/support point)
3. **Drag** to select the pendulum mass (ROI)
4. Tracking begins automatically
5. Press **'q'** to stop and save data

**Output files:**
- `live_track_TIMESTAMP.csv` - Position and angle data
- `live_track_amplitude_TIMESTAMP.png` - Amplitude decay plot
- `live_track_metadata_TIMESTAMP.csv` - Experimental metadata

### Mode 2: Process Video File
Analyze pre-recorded video:

```bash
python test_integration.py --mode video \
  --video path/to/your/video.mp4 \
  --experiment 1
```

**Steps:**
1. Video opens in a window
2. **Click** to select equilibrium point
3. **Drag** to select the pendulum mass
4. Processing begins automatically

### Mode 3: Validation Tests Only
Run all system tests without hardware:

```bash
python test_integration.py --mode validate
```

## Available Experiments

| Experiment | Hilo Length | Area Condition | Description |
|------------|------------|---|---|
| 1 | 30 cm | sin_hojas | Without leaves |
| 2 | 30 cm | con_hojas | With leaves |
| 3 | 40 cm | sin_hojas | Longer string, no leaves |
| 4 | 40 cm | con_hojas | Longer string, with leaves |

## Direct Usage (Advanced)

### Using liveTrack.py directly:
```bash
python liveTrack.py --source 0 \
  --hilo-length 30 \
  --area-condition sin_hojas \
  --output-dir ./tracking_output
```

### Available trackers:
- `KCF` (default) - Fast, balanced
- `CSRT` - More accurate but slower
- `MOSSE` - Fastest

```bash
python liveTrack.py --tracker CSRT --source 0
```

## Output Files

### CSV Format
**live_track_TIMESTAMP.csv:**
- `Time(s)` - Timestamp in seconds
- `X` - Horizontal displacement in pixels
- `Y` - Vertical displacement in pixels
- `Angle(deg)` - Calculated angle in degrees

**live_track_metadata_TIMESTAMP.csv:**
- Hilo length
- Area condition
- Damping coefficient (β)
- Quality factor (Q)
- Oscillation period
- Fit statistics

### Plots
**live_track_amplitude_TIMESTAMP.png:**
- Raw and smoothed angle signal
- Amplitude envelope
- Exponential decay fit
- Peak detection visualization

## Physics Behind the Tracking

### Angle Calculation
$$\theta = \arcsin\left(\frac{x_c - x_0}{L_{px}}\right)$$

Where:
- $x_c$ = horizontal position of mass center
- $x_0$ = equilibrium point x-coordinate
- $L_{px}$ = string length in pixels

### Damping Analysis
$$A(t) = A_0 \cdot e^{-\beta t}$$

Where:
- $A(t)$ = amplitude at time t
- $\beta$ = damping coefficient
- $A_0$ = initial amplitude

## Troubleshooting

### No webcam detected
```bash
# Use a different video source
python test_integration.py --mode live --video 1
```

### Tracking fails during video
- Try a different tracker: `--tracker CSRT`
- Ensure good lighting
- Object should contrast with background

### Files not saving
- Check output directory permissions
- Ensure output directory exists:
```bash
mkdir tracking_output
```

### Import errors
Reinstall requirements:
```bash
pip install --upgrade -r requirements.txt
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Stop tracking and save |
| `ESC` | Stop tracking (video mode) |
| Mouse Click | Select equilibrium point |
| Mouse Drag | Select object region |

## Example Workflow

```bash
# 1. Validate your setup
python test_integration.py --mode validate

# 2. Run live tracking
python test_integration.py --mode live --experiment 1

# 3. Process multiple experiments
for exp in 1 2 3 4; do
  python test_integration.py --mode live --experiment $exp --output-dir results/exp_$exp
done
```

## Performance Tips

1. **Better tracking accuracy:**
   - Use CSRT tracker (slower but more accurate)
   - Ensure good lighting
   - Use contrasting colored object

2. **Faster processing:**
   - Use MOSSE tracker
   - Reduce camera resolution
   - Close other applications

3. **Better data quality:**
   - Record longer oscillations (30+ seconds)
   - Ensure stable camera
   - Minimize vibrations

## Data Analysis

Once data is captured, use pandas to analyze:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('tracking_output/live_track_TIMESTAMP.csv')

# Plot angle over time
plt.figure(figsize=(12, 6))
plt.plot(df['Time(s)'], df['Angle(deg)'])
plt.xlabel('Time (s)')
plt.ylabel('Angle (degrees)')
plt.title('Pendulum Angle vs Time')
plt.grid(True)
plt.show()

# Calculate statistics
print(f"Max angle: {df['Angle(deg)'].abs().max():.2f}°")
print(f"Oscillation frequency: {1/period:.2f} Hz")
```

## References

- OpenCV Documentation: https://docs.opencv.org/
- SciPy Signal Processing: https://docs.scipy.org/doc/scipy/reference/signal.html
- Physics of Damped Oscillations: https://en.wikipedia.org/wiki/Damping_ratio

---

**Version:** 1.0  
**Last Updated:** 2024  
**Author:** Pendulum Tracking Team
