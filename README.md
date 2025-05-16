# TianyuControl - Astronomical Equipment Control System

TianyuControl is a comprehensive astronomical equipment monitoring and control system that provides management functionality for telescopes and related peripherals. Developed with Python and PyQt5, it supports ASCOM standard devices and offers an intuitive graphical user interface. Suitable for observatories, research institutions, and astronomy enthusiasts.

## Features

### Core Functions

- **Unified Device Management**: Centrally manage telescopes, focusers, rotators, weather stations, covers, domes, cooling systems, and UPS.
- **Real-time Status Monitoring**: Automatically retrieve and display operating status and parameters of various devices.
- **Remote Control**: Operate telescopes and peripheral equipment remotely through the Alpaca API.
- **Multilingual Support**: Support switching between Chinese and English, with expandability for other languages.
- **Theme Switching**: Provide day mode, night mode, and red light mode to adapt to different observation environments.

### Device Support

#### Telescope Control
- Display telescope coordinates: right ascension, declination, altitude, azimuth.
- Monitor telescope status: tracking, guiding, slewing, homing.
- Display motor enable status.
- Support coordination with other devices (e.g., dome).

#### Focuser Control
- Monitor focuser position, temperature, and movement status.
- Support movement to specified positions and emergency stop.
- Display current position relative to maximum travel range.
- Support focuser temperature compensation monitoring.

#### Rotator Monitoring
- Display rotator angle.
- Calculate frame-declination angle.
- Angle visualization and real-time parallactic angle calculation.
- Support DSS image overlay with angle visualization.

#### Dome Control
- Monitor dome status: azimuth, position status (home, parked, slewing).
- Shutter status monitoring: open, closed, moving, error.
- Shutter open/close control.
- Intelligent button state management: automatically enable/disable buttons based on dome status.

#### Cover Control
- Monitor cover status: open, closed, moving, error.
- Provide cover open/close buttons with dynamic control based on status.
- Status change feedback and visual cues.
- Support one-click operation with synchronized status display.

#### Weather Station Monitoring
- Display comprehensive environmental parameters: cloud cover, dew point, humidity, pressure, rainfall.
- Sky brightness, sky temperature, seeing, air temperature, wind direction and speed monitoring.
- Provide visual indicators based on value ranges (safe/dangerous states).
- Support multiple weather station devices.

#### Cooling System Monitoring
- Real-time temperature monitoring.
- Monitor running status, flow alarms, temperature alarms, level alarms, and power status.
- Serial data communication with standard protocol support.
- Highlight abnormal states with alarm functions.

#### UPS Power Monitoring
- UPS status, output voltage, battery level, and temperature monitoring.
- Health status and operating mode monitoring.
- Low battery alerts.
- Status change history.

### Additional Features

#### Time Information
- Display local time and date.
- UTC+8 time display.
- Calculate sunrise and sunset times.
- Calculate twilight times (astronomical, nautical, civil).
- Moon phase display.
- Solar altitude display.
- Astronomical observation timing suggestions.

#### All-Sky Camera Integration
- Support all-sky camera image display.
- Scheduled image refresh.
- Adaptive image scaling.
- Memory-optimized image processing.

#### Device Management
- Automatic device discovery and connection.
- Support for automatic detection of serial devices.
- Device connection status management.
- Convenient reconnection and disconnection.
- Dynamic device menu updates.

#### DSS Image Retrieval
- Support DSS (Digital Sky Survey) image retrieval based on coordinates.
- Image integration with angle visualization.
- Target area star chart display.
- Rotator angle visualization assistance.

## System Architecture

TianyuControl adopts a modular architecture design, primarily consisting of the following components:

- **Main Window Module**: Provides core user interface and interaction logic.
- **Device Services**: Responsible for communication with various astronomical devices.
- **Astronomical Calculation Service**: Provides astronomical calculation functionality.
- **API Client**: Implements communication with ASCOM Alpaca devices.
- **Internationalization Support**: Provides multilingual translation functionality.
- **Theme Management**: Implements multi-theme switching.
- **Device Controllers**: Specialized control logic for each device type.
- **Event System**: Signal and slot mechanism for component communication.
- **Data Storage**: Configuration information and device status storage.

### Directory Structure

```
TianyuControl/
├── main.py                  # Program entry
├── device_manager.py        # Device manager
├── api_client.py            # Alpaca API client
├── utils/                   # Utility functions
│   ├── i18n.py              # Internationalization tools
│   ├── theme_manager.py     # Theme management
│   └── ...
├── src/
│   ├── ui/                  # User interface
│   │   ├── main_window.py   # Main window
│   │   ├── components/      # UI components
│   │   └── ...
│   ├── services/            # Service modules
│   │   ├── astronomy_service.py  # Astronomical calculation service
│   │   ├── device_service.py     # Device service
│   │   └── ...
│   └── config/              # Configuration module
└── docs/                    # Documentation directory
```

## Technical Features

- Modern graphical interface built with PyQt5.
- Device communication using ASCOM Alpaca standard.
- Real-time data acquisition and status updates.
- Responsive design, supporting window size adjustment.
- Memory monitoring and leak detection.
- Optimized memory management and performance tuning.
- Multi-threaded processing ensures UI responsiveness.
- Signal-slot mechanism for inter-component communication.
- State-based UI update strategy.
- Exception handling and logging.

## System Requirements

- Python 3.6+
- PyQt5
- PySerial (for serial device communication)
- ASCOM standard-compliant astronomical devices
- Operating System: Windows 10+ (primary support), Linux and macOS (partial functionality)
- Display Resolution: 1920×1080 or higher recommended
- Minimum Hardware Requirements:
  - CPU: Dual-core 2.0GHz+
  - RAM: 4GB+
  - Disk Space: 200MB+

## Installation Guide

### Installing Dependencies

```bash
# Clone the project
git clone https://github.com/yourusername/TianyuControl.git
cd TianyuControl

# Install dependencies
pip install -r requirements.txt
```

### ASCOM Platform Setup

1. Ensure the ASCOM platform is installed (Windows system)
2. Install ASCOM drivers for required devices
3. Configure Alpaca server for remote devices

### Configuration

1. Copy `config/config.example.json` to `config/config.json`
2. Edit the configuration file to set device API addresses and parameters:

```json
{
  "devices": {
    "telescope": {
      "api_url": "http://your-alpaca-server:11111"
    },
    "dome": {
      "api_url": "http://your-alpaca-server:11111"
    },
    "covercalibrator": {
      "api_url": "http://your-alpaca-server:11111"
    },
    "focuser": {
      "api_url": "http://your-alpaca-server:11111"
    },
    "cooler": {
      "port": "COM3",
      "baudrate": 9600
    },
    "ups": {
      "port": "COM4",
      "baudrate": 9600
    },
    "allsky_camera": {
      "enabled": true,
      "image_path": "/path/to/camera/images/",
      "image_name": "latest",
      "image_extension": ".jpg",
      "refresh_interval": 5
    }
  }
}
```

## Usage Instructions

1. After starting the program, the system will automatically search for available ASCOM devices
   ```bash
   python main.py
   ```

   Advanced startup options:
   ```bash
   # Enable memory monitoring
   python main.py --monitor-memory
   
   # Enable memory optimization mode
   python main.py --optimize-memory
   
   # Enable debug mode
   python main.py --debug
   
   # Custom memory check and garbage collection intervals (milliseconds)
   python main.py --monitor-memory --check-interval 10000 --gc-interval 120000
   
   # Combined usage
   python main.py --monitor-memory --optimize-memory --debug
   ```

2. Use the "Connect" menu at the top of the interface to connect to required devices
   - Select the corresponding device type
   - Select the specific device instance
   - Click to connect

3. After connection, the system will automatically begin monitoring device status and display it on the interface
   - Telescope status area displays coordinates and operating status
   - Environmental monitoring area displays meteorological information
   - Dome, cover, and other device statuses update in real-time

4. Use the buttons in each device control area for operations
   - Cover open/close
   - Dome open/close
   - Focuser movement control

5. Language and theme can be switched through the "Settings" menu
   - Day mode: Suitable for daytime use
   - Night mode: Dark theme to reduce light pollution
   - Red light mode: Preserves night vision

## Application Scenarios

### Observatory Automation

TianyuControl is particularly suitable for observatory automation management, allowing centralized control of all observatory devices for one-stop management:

- Remote opening/closing of the dome
- Management of telescope tracking status
- Monitoring of environmental parameters to ensure observation conditions
- Control of peripheral devices such as covers, focusers, etc.

### Scientific Observation

For astronomical researchers, the system provides professional device control and data monitoring functions:

- Precise control of telescope pointing
- Real-time monitoring of seeing and environmental parameters
- Preview of observation targets through DSS images
- Acquisition of professional parameters such as parallactic angle

### Educational and Amateur Use

For educational institutions and astronomy enthusiasts, the system provides a friendly interface and comprehensive information display:

- Multilingual support facilitates international exchange
- Astronomical time information (sunrise/sunset, twilight times, etc.)
- Intuitive status display and visualization
- All-sky camera integration for quick sky condition assessment

## Frequently Asked Questions

### Device Connection Issues

**Q: The program cannot find my device. How do I resolve this?**

A: Please check the following:
- Confirm the device is properly connected to the computer
- Confirm that the ASCOM driver for the corresponding device is installed
- For network devices, confirm that the Alpaca server is running and the network connection is normal
- Use the "Refresh Device List" function to rescan for devices

**Q: What should I do if serial devices (cooling system, UPS) cannot connect?**

A: Please check:
- Confirm the serial port is visible in the system device manager
- Confirm the serial port baud rate matches the device
- Check if the device is being used by another program
- Try restarting the device and computer

### Functionality Issues

**Q: What should I do if the cover or dome control buttons are disabled?**

A: This is usually because:
- The current device state does not allow the operation (e.g., the open button is disabled when the cover is already open)
- The device is in motion and you need to wait for the operation to complete
- The device is in an error state, requiring inspection and possibly manual intervention

**Q: How do I configure the all-sky camera function?**

A: In the configuration file:
- Ensure the `enabled` parameter in the `allsky_camera` section is set to `true`
- Set the correct image path and filename
- Adjust the refresh interval as needed
- Restart the program to apply changes

### Performance Issues

**Q: The program becomes slow after running for a while. How do I fix this?**

A: Possible solutions:
- Reduce connections to unnecessary devices to lower monitoring load
- Increase the refresh interval for the all-sky camera
- Check computer resource usage and close other unnecessary programs
- Use the memory monitoring and optimization features
- Restart the program to release potential memory leaks

## Memory Management

The TianyuControl system includes built-in memory optimization and monitoring to ensure stable operation during long observing sessions. Memory management is **enabled by default** and optimized for long-term operation.

### Memory Features

- **Automatic Memory Optimization**: The system is configured to perform regular garbage collection and optimize memory usage.
- **Memory Usage Monitoring**: Real-time monitoring of application memory usage.
- **Leak Detection**: Identifies potential memory leaks and circular references.
- **Detailed Logging**: Memory-related events are logged to files for later analysis.

### Advanced Startup Options

Memory management can be controlled through command-line options:

```
python main.py [options]
```

Available options:

- `--monitor-memory`: Memory monitoring is enabled by default. Use this flag to disable it.
- `--optimize-memory`: Memory optimization is enabled by default. Use this flag to disable it.
- `--debug`: Enable debug mode with detailed logging.
- `--check-interval SECONDS`: Set memory check interval in seconds (default: 30)
- `--gc-interval SECONDS`: Set garbage collection interval in seconds (default: 60)
- `--no-gc-log`: Disable garbage collection logging

### Log Files

Memory-related logs are stored in the `logs` directory:
- `gc_YYYYMMDD_HHMMSS.log`: Contains garbage collection events
- `debug_YYYYMMDD_HHMMSS.log`: Contains detailed debug information (when debug mode is enabled)

### Memory Statistics

Memory statistics are printed to the console during operation and when the application exits. The statistics include:

- **RSS (Resident Set Size)**: Amount of memory currently used by the application
- **Memory growth rate**: Rate of memory growth over time
- **System memory percentage**: Percentage of total system memory used by the application

### Memory Diagnostic Tool

The TianyuControl package includes a memory diagnostic tool to help identify and resolve memory issues. This tool can be run separately from the main application to analyze memory usage, detect leaks, and generate diagnostic reports.

#### Using the Memory Diagnostic Tool

To generate a complete diagnostic report:

```
python memory_diagnose.py --report
```

This will create a comprehensive report file named `memory_diagnosis_YYYYMMDD_HHMMSS.txt` that includes:
- System resource analysis
- Running TianyuControl process analysis
- Memory fragmentation checks
- Object allocation statistics
- Memory leak detection
- Diagnostic recommendations

#### Advanced Diagnostic Options

The diagnostic tool supports multiple targeted analysis options:

```
python memory_diagnose.py --find-process    # Find running TianyuControl processes
python memory_diagnose.py --check-pid 1234  # Analyze a specific process by PID
python memory_diagnose.py --system          # System resource analysis only
python memory_diagnose.py --objects         # Memory object analysis
python memory_diagnose.py --leaks           # Memory leak detection
python memory_diagnose.py --fragmentation   # Memory fragmentation analysis
```

You can specify a custom output file for the report:

```
python memory_diagnose.py --report --output custom_report.txt
```

#### When to Use the Diagnostic Tool

- When experiencing memory-related performance issues
- If the application freezes during long observation sessions
- To verify that memory optimization is working correctly
- When troubleshooting system resource limitations

## How to Contribute

TianyuControl is an open-source project, and we welcome contributions in various forms:

1. Report Bugs: Report issues encountered in GitHub Issues
2. Submit Improvement Suggestions: Propose feature requests or improvement suggestions through Issues
3. Submit Code:
   - Fork this project
   - Create a feature branch (`git checkout -b feature/amazing-feature`)
   - Commit changes (`git commit -m 'Add some amazing feature'`)
   - Push to the branch (`git push origin feature/amazing-feature`)
   - Submit a Pull Request

### Development Guidelines

- Code style follows PEP 8 specifications
- New features require corresponding documentation and comments
- Run tests before submission to ensure code quality
- Adding new device support requires implementing standard interfaces

## License

TianyuControl follows the MIT license - see the [LICENSE](LICENSE) file for details

## Contact Information

- Project Maintainer: [Your Name](mailto:your.email@example.com)
- Project Homepage: [GitHub Project Address](https://github.com/yourusername/TianyuControl)