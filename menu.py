#!/usr/bin/env python3
"""
Pendulum Tracking System - Interactive Menu
Provides an easy-to-use interface for running tracking experiments
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header():
    print("\n" + "=" * 70)
    print("🎯 PENDULUM TRACKING SYSTEM - INTERACTIVE MENU")
    print("=" * 70 + "\n")

def print_menu():
    print("Select an option:")
    print("  1. Run validation tests")
    print("  2. Start live webcam tracking")
    print("  3. Process video file")
    print("  4. View help and examples")
    print("  5. Exit")
    print()

def run_validation():
    print("\n▶️  Running validation tests...\n")
    cmd = [sys.executable, "test_integration.py", "--mode", "validate"]
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def run_live_tracking():
    print("\n📹 LIVE WEBCAM TRACKING")
    print("-" * 70)
    
    # Experiment selection
    print("\nAvailable Experiments:")
    experiments = {
        1: ("30 cm", "sin_hojas", "Experiment 1 - 30cm without leaves"),
        2: ("60 cm", "sin_hojas", "Experiment 2 - 60cm without leaves"),
        3: ("30 cm", "con_hojas", "Experiment 3 - 30cm with leaves"),
        4: ("60 cm", "con_hojas", "Experiment 4 - 60cm with leaves"),
    }
    
    for num, (length, condition, desc) in experiments.items():
        print(f"  {num}. {desc}")
    
    try:
        exp_choice = int(input("\nSelect experiment (1-4): "))
        if exp_choice not in experiments:
            print("❌ Invalid choice!")
            return False
    except ValueError:
        print("❌ Invalid input!")
        return False
    
    # Tracker selection
    print("\nAvailable Trackers:")
    print("  1. KCF (default - balanced)")
    print("  2. CSRT (accurate but slower)")
    print("  3. MOSSE (fastest)")
    
    tracker_map = {1: "KCF", 2: "CSRT", 3: "MOSSE"}
    try:
        tracker_choice = int(input("\nSelect tracker (1-3) [default: 1]: ") or "1")
        tracker = tracker_map.get(tracker_choice, "KCF")
    except ValueError:
        tracker = "KCF"
    
    # Output directory
    output_dir = input("\nOutput directory [./tracking_output]: ").strip() or "./tracking_output"
    
    print(f"\n✓ Configuration:")
    print(f"  Experiment: {exp_choice}")
    print(f"  Tracker: {tracker}")
    print(f"  Output directory: {output_dir}")
    
    confirm = input("\nStart tracking? (y/n) [y]: ").strip().lower() or "y"
    if confirm != "y":
        print("Cancelled.")
        return False
    
    print("\n▶️  Starting live tracking...\n")
    cmd = [
        sys.executable, 
        "test_integration.py", 
        "--mode", "live",
        "--experiment", str(exp_choice),
        "--output-dir", output_dir
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def run_video_processing():
    print("\n🎬 VIDEO FILE PROCESSING")
    print("-" * 70)
    
    video_path = input("\nEnter video file path: ").strip()
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        return False
    
    # Experiment selection
    print("\nAvailable Experiments:")
    for num in range(1, 5):
        print(f"  {num}. Experiment {num}")
    
    try:
        exp_choice = int(input("\nSelect experiment (1-4): "))
        if exp_choice not in range(1, 5):
            print("❌ Invalid choice!")
            return False
    except ValueError:
        print("❌ Invalid input!")
        return False
    
    output_dir = input("\nOutput directory [./tracking_output]: ").strip() or "./tracking_output"
    
    print(f"\n✓ Configuration:")
    print(f"  Video: {video_path}")
    print(f"  Experiment: {exp_choice}")
    print(f"  Output directory: {output_dir}")
    
    confirm = input("\nStart processing? (y/n) [y]: ").strip().lower() or "y"
    if confirm != "y":
        print("Cancelled.")
        return False
    
    print("\n▶️  Starting video processing...\n")
    cmd = [
        sys.executable,
        "test_integration.py",
        "--mode", "video",
        "--video", video_path,
        "--experiment", str(exp_choice),
        "--output-dir", output_dir
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0

def show_help():
    print("""
📚 HELP AND EXAMPLES
═════════════════════════════════════════════════════════════════

1. LIVE WEBCAM TRACKING
   • Captures real-time data from webcam
   • Automatically calculates angles and damping
   • Saves CSV data and plots
   
   Steps:
   1. Click on the equilibrium (pivot) point
   2. Drag to select the pendulum mass
   3. Press 'q' when done to save data

2. VIDEO PROCESSING
   • Analyzes pre-recorded video files
   • Same analysis as live tracking
   • Useful for batch processing

3. OUTPUT FILES
   • CSV files with tracking data
   • PNG plots with amplitude analysis
   • Metadata CSV with experimental parameters

4. KEYBOARD SHORTCUTS
   • 'q' - Stop tracking and save
   • ESC - Stop tracking (video mode)
   • Mouse click - Select equilibrium point
   • Mouse drag - Select tracking region

📖 For detailed documentation:
   Read: README_TRACKING.md
   
💡 Command-line usage:
   python test_integration.py --help
   
═════════════════════════════════════════════════════════════════
    """)
    input("\nPress Enter to continue...")

def main():
    # Check if test_integration.py exists
    if not os.path.exists("test_integration.py"):
        print("❌ Error: test_integration.py not found!")
        print("   Make sure you're in the Tracker_Pendulo directory")
        sys.exit(1)
    
    while True:
        print_header()
        print_menu()
        
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                success = run_validation()
                if success:
                    print("\n✅ Tests completed!")
                else:
                    print("\n⚠️  Tests finished with errors")
            
            elif choice == "2":
                success = run_live_tracking()
                if success:
                    print("\n✅ Tracking completed!")
                else:
                    print("\n⚠️  Tracking ended")
            
            elif choice == "3":
                success = run_video_processing()
                if success:
                    print("\n✅ Processing completed!")
                else:
                    print("\n⚠️  Processing ended")
            
            elif choice == "4":
                show_help()
            
            elif choice == "5":
                print("\n👋 Goodbye!")
                sys.exit(0)
            
            else:
                print("\n❌ Invalid choice!")
                continue
            
            input("\n[Press Enter to continue]")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\n[Press Enter to continue]")

if __name__ == "__main__":
    main()
