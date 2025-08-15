#!/usr/bin/env python3
"""
Fall Detection System Launcher
Provides easy access to all system components
"""

import sys
import subprocess
import os

def get_python_path():
    """Get the correct Python path for the virtual environment."""
    return "/Users/andycyw/mvp_fall_detection_starter/.venv/bin/python"

def run_tests():
    """Run compatibility tests."""
    print("🧪 Running compatibility tests...")
    subprocess.run([get_python_path(), "test_compatibility.py"])

def run_main_app():
    """Run the main fall detection application."""
    print("🚀 Starting main fall detection application...")
    print("Camera window will open. Press 'q' to quit, 'r' to reset.")
    subprocess.run([get_python_path(), "main_compatible.py"])

def run_dashboard():
    """Run the Streamlit dashboard."""
    print("🌐 Starting web dashboard...")
    print("Dashboard will open in your browser at http://localhost:8501")
    subprocess.run([get_python_path(), "-m", "streamlit", "run", "ui_dashboard.py"])

def show_menu():
    """Display the main menu."""
    print("\n" + "="*60)
    print("🎯 FALL DETECTION SYSTEM - LAUNCHER")
    print("="*60)
    print("Choose an option:")
    print()
    print("1. 🧪 Run Tests (recommended first)")
    print("2. 🚀 Main Application (real-time detection)")
    print("3. 🌐 Web Dashboard (testing interface)")
    print("4. ℹ️  System Information")
    print("5. 📝 Quick Help")
    print("6. 🚪 Exit")
    print()

def show_system_info():
    """Show system information."""
    print("\n📊 SYSTEM INFORMATION")
    print("-" * 40)
    
    # Python version
    result = subprocess.run([get_python_path(), "--version"], 
                          capture_output=True, text=True)
    print(f"Python: {result.stdout.strip()}")
    
    # Check key components
    components = {
        "OpenCV": "cv2",
        "NumPy": "numpy", 
        "Streamlit": "streamlit",
        "SoundDevice": "sounddevice",
        "Plotly": "plotly"
    }
    
    print("\nInstalled Components:")
    for name, module in components.items():
        try:
            subprocess.run([get_python_path(), "-c", f"import {module}"], 
                          check=True, capture_output=True)
            print(f"✅ {name}")
        except subprocess.CalledProcessError:
            print(f"❌ {name}")
    
    print(f"\nWorking Directory: {os.getcwd()}")
    print(f"Virtual Environment: {get_python_path()}")

def show_help():
    """Show quick help information."""
    print("\n📝 QUICK HELP")
    print("-" * 40)
    print("🧪 Tests: Verify all components work")
    print("🚀 Main App: Real-time camera + audio detection")
    print("🌐 Dashboard: Web interface for testing")
    print()
    print("Key Features:")
    print("• Motion-based fall detection (no MediaPipe needed)")
    print("• Audio volume monitoring for help calls")
    print("• Smart alert system with cooldown")
    print("• Compatible with Python 3.13")
    print()
    print("Controls (Main App):")
    print("• Press 'q' to quit")
    print("• Press 'r' to reset detection")
    print("• Camera shows live feed with motion tracking")
    print()
    print("Troubleshooting:")
    print("• Camera not working? Check System Preferences > Privacy")
    print("• Audio issues? Check microphone permissions")
    print("• Test first with option 1 to verify setup")

def main():
    """Main launcher function."""
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == "1":
                run_tests()
            elif choice == "2":
                run_main_app()
            elif choice == "3":
                run_dashboard()
            elif choice == "4":
                show_system_info()
            elif choice == "5":
                show_help()
            elif choice == "6":
                print("\n👋 Goodbye!")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
