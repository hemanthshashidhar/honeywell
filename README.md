# SecureScope

SecureScope is a real-time security monitoring dashboard built with Streamlit. It combines SSH log monitoring, a local honeypot file, host resource visibility, and live packet inspection through `tshark` to highlight suspicious activity on a Linux machine.

The project is currently implemented as a single Python application in [`securescope.py`](/home/hemanth/honeywell/securescope.py) with a small dependency set in [`requirements.txt`](/home/hemanth/honeywell/requirements.txt).

## What It Does

- Monitors recent SSH login activity from the system auth log
- Classifies events as `FAILED`, `INVALID`, or `SUCCESS`
- Detects repeated failed attempts from the same IP inside a 5-minute window
- Raises in-app alerts for brute-force patterns, honeypot access, and successful logins
- Creates and watches a decoy file at `~/SECRET_CLASSIFIED.txt`
- Displays current CPU load, memory usage, and disk usage for the local host
- Captures live IP packets with `tshark`
- Detects packet anomalies such as port scans, SYN bursts, SSH hammering, ICMP spikes, and traffic spikes
- Resolves public IP addresses to approximate geolocation data
- Displays a live dashboard with metrics, event tables, alerts, and a map
- Auto-refreshes every 3 seconds

## Dashboard Sections

- Hero status bar showing active monitoring targets
- Alert banners for the latest critical events across SSH, honeypot, and network traffic
- SSH and host monitoring section
- Host resource monitor panel
- Honeypot file activity table
- Attacker geolocation map
- Network packet summary, anomaly table, and recent packet activity table

## How It Works

### 1. SSH Log Monitoring

SecureScope tails the latest 500 lines from `/var/log/auth.log` and parses SSH-related entries. It looks for:

- Failed password attempts
- Accepted password or public key logins
- Invalid user attempts

Each event is normalized into a structured record with timestamp, source IP, username, port, authentication method, and status.

### 2. Brute-Force Detection

Failed and invalid attempts are grouped by source IP. If the same IP reaches at least 5 failures within 5 minutes, the source is flagged as a brute-force candidate and surfaced in the UI.

### 3. Honeypot Monitoring

On startup, the app creates a decoy file at `~/SECRET_CLASSIFIED.txt` if it does not already exist. A filesystem watcher monitors that file and records activity such as modification or access-related events in the dashboard.

### 4. Host Resource Monitoring

The dashboard reads local system information to show:

- CPU load average normalized against available CPU cores
- Memory usage from `/proc/meminfo`
- Home-directory disk usage

### 5. Packet Monitoring And Anomaly Detection

SecureScope starts a background `tshark` process on interface `any` and reads line-buffered packet metadata. It captures a rolling window of recent IP traffic and normalizes each packet into:

- Timestamp
- Source IP and destination IP
- Source and destination port
- Protocol
- Packet length
- TCP SYN / ACK flags
- Direction relative to the local host

It then applies rule-based anomaly checks over the last 60 seconds:

- Port scan: one source IP touches many destination ports quickly
- SYN burst: one source IP sends many TCP SYN packets
- SSH hammering: one source IP sends repeated traffic to port `22`
- ICMP spike: one source IP sends a burst of ICMP traffic
- Traffic spike: aggregate suspicious traffic volume suddenly increases

### 6. IP Geolocation

For public IPs, the app queries `ip-api.com` and plots successful lookups on the built-in Streamlit map. Private and loopback addresses are intentionally skipped.

## Tech Stack

- Python
- Streamlit
- pandas
- requests
- watchdog
- streamlit-autorefresh

## Project Structure

```text
honeywell/
├── README.md
├── requirements.txt
└── securescope.py
```

## Requirements

- Python 3.10+ recommended
- Linux environment with SSH authentication logs available at `/var/log/auth.log`
- Network access for geolocation lookups to `http://ip-api.com`
- Permission to read `/var/log/auth.log`
- `tshark` installed and permitted to capture packets on the host

The local virtual environment in this repository was created with Python 3.13.5.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run securescope.py
```

Then open the local Streamlit URL shown in the terminal, typically:

```text
http://localhost:8501
```

If packet capture fails, the dashboard will still load, but the network packet section will show the `tshark` error message. On many Linux systems, packet capture requires elevated privileges or Linux capabilities for the `tshark` binary.

## Using the Honeypot

The app watches the following file:

```text
~/SECRET_CLASSIFIED.txt
```

To generate a test event after starting the app, interact with the file from another terminal:

```bash
cat ~/SECRET_CLASSIFIED.txt
echo "# test" >> ~/SECRET_CLASSIFIED.txt
```

Depending on the filesystem event produced on your machine, SecureScope will record the activity in the honeypot panel and add an alert.

## Testing With Two Systems

Use a simple lab setup:

- System A: runs SecureScope
- System B: generates test traffic toward System A

Public IPs are not required for packet detection. Private LAN IPs and loopback traffic can trigger the packet anomaly rules too. Only the geolocation map needs public IPs.

Start SecureScope on System A:

```bash
streamlit run securescope.py
```

Then generate traffic from System B.

Normal traffic:

```bash
ping <system-a-ip>
ssh <user>@<system-a-ip>
```

Port-scan style traffic:

```bash
nmap -Pn <system-a-ip>
```

SYN-scan style traffic:

```bash
nmap -sS <system-a-ip>
```

SSH hammering test:

```bash
for i in $(seq 1 20); do ssh invalid@<system-a-ip>; done
```

ICMP spike test:

```bash
ping -c 40 <system-a-ip>
```

Expected results:

- SSH failures appear in the SSH monitor
- Port and SYN scans appear in the packet anomaly section
- Repeated SSH packet traffic raises `SSH Hammering`
- ICMP bursts raise `ICMP Spike`
- The recent packet table shows the source and destination IPs involved

## Configuration Embedded in the App

The current implementation uses fixed values defined in code:

- Auth log path: `/var/log/auth.log`
- Honeypot file: `~/SECRET_CLASSIFIED.txt`
- Packet capture interface: `any`
- Refresh interval: `3000 ms`
- Brute-force threshold: `5` failures
- Brute-force window: `5 minutes`
- Auth log tail size: `500` lines
- Max alert history: `8`
- Max honeypot events stored: `50`
- Max packet events stored in memory: `1200`
- Packet retention window: `10 minutes`
- Packet anomaly window: `60 seconds`

## Current Limitations

- The log parser expects a specific auth log format and may not match all Linux distributions
- The regex currently targets `sshd-session[...]` log lines, so systems with different SSH log prefixes may produce fewer matches
- The app depends on `/var/log/auth.log`, which is not present on every Linux setup
- Packet capture depends on `tshark` and the current user having capture permissions
- Packet anomaly detection is threshold-based, not signature-based IDS logic
- Only packet metadata is inspected; there is no payload analysis
- Geolocation requires outbound HTTP access and depends on a third-party service
- There is no persistence layer; data is kept in Streamlit session state during runtime
- There are no automated tests yet
- The project is a single-file application, so configuration and UI logic are tightly coupled

## Possible Next Improvements

- Move hard-coded settings into environment variables or a config file
- Support more auth log formats and distro variants
- Add persistent event storage
- Add filtering, search, and export in the dashboard
- Add tests for parsing and brute-force detection
- Split the code into modules for UI, parsing, detection, and integrations

## Repository Context

This repository currently contains one main application file and a Python virtual environment directory. The virtual environment should generally not be committed to GitHub. If you plan to publish this repository, keep the tracked source files minimal and add a `.gitignore` for environment and cache artifacts if needed.
