# Pinglo

<div align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-blue.svg" alt="Platform: Windows">
  <img src="https://img.shields.io/badge/Python-3.6+-green.svg" alt="Python: 3.6+">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</div>

<p align="center">
  <b>Minimalist utility for monitoring and logging ping responses from IP addresses</b>
</p>

## 📋 Description

**Pinglo** is a compact Windows GUI utility designed for monitoring IP address availability using the ping command and logging the results. The program allows you to track multiple IP addresses simultaneously, customize the check interval, and choose the logging mode.

![Pinglo Screenshot](https://via.placeholder.com/800x450.png?text=Pinglo+Screenshot)

## ✨ Features

- **Multiple IP monitoring** — simultaneously track the availability of multiple IP addresses
- **Flexible interval settings** — set the frequency of checks in seconds
- **Two logging modes**:
  - Combined file for all IP addresses
  - Separate files for each IP address
- **CSV import** — quickly add a list of IP addresses from a CSV file
- **Real-time log display** — view ping results directly in the interface
- **Modern interface** — minimalist and user-friendly design

## 🚀 Installation and Launch

### Requirements

- Windows 10 or newer
- Python 3.6+
- tkinter library (usually included in the standard Python installation for Windows)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pinglo.git
   cd pinglo
   ```

2. Install dependencies (if necessary):
   ```bash
   pip install -r requirements.txt
   ```

### Launch

```bash
python ping_monitor.py
```

### Executable Version

You can also use the standalone executable version:
1. Download `Pinglo.exe` from the releases section
2. Run the executable - no installation required

## 📝 Usage

1. **Adding IP addresses**:
   - Enter an IP address in the input field and click "Add IP"
   - Or import a list of addresses from a CSV file by clicking "Import from CSV"

2. **Setting ping interval**:
   - Specify the interval in seconds in the "Ping Interval" field

3. **Choosing logging mode**:
   - "Combined File" — all logs in one file
   - "Separate Files" — separate file for each IP

4. **Starting monitoring**:
   - Click the "Start" button to begin monitoring
   - Click "Stop" to end monitoring

5. **Viewing logs**:
   - Results are displayed in the right part of the interface
   - Logs are also saved in the `logs` folder in the program directory

### CSV File Format

The CSV file should contain IP addresses in the first column, one address per line:

```
192.168.1.1
8.8.8.8
172.17.15.15
```

## 📁 Project Structure

```
pinglo/
├── ping_monitor.py   # Main program file
├── requirements.txt  # Project dependencies
├── README.md         # Documentation
└── logs/             # Logs folder (created automatically)
    ├── ping_log.txt  # Combined log file
    └── ping_log_*.txt # Separate log files for each IP
```

## 🔧 Configuration

The program requires no additional configuration and is ready to use immediately after launch.

## 📄 License

Distributed under the MIT License. See the `LICENSE` file for more information.

## 🙏 Acknowledgments

- Thanks to everyone who contributed to the project
- Inspired by the need for a simple and effective tool for monitoring network devices
