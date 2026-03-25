# SecureScope

SecureScope is a real-time SSH security monitoring dashboard built with Streamlit. It reads recent authentication activity from `/var/log/auth.log`, detects likely brute-force behavior, watches a decoy honeypot file for local access attempts, and visualizes geolocatable attacker IPs on a live map.

The project is currently implemented as a single Python application in [`securescope.py`](/home/hemanth/honeywell/securescope.py) with a small dependency set in [`requirements.txt`](/home/hemanth/honeywell/requirements.txt).

## What It Does

- Monitors recent SSH login activity from the system auth log
- Classifies events as `FAILED`, `INVALID`, or `SUCCESS`
- Detects repeated failed attempts from the same IP inside a 5-minute window
- Raises in-app alerts for brute-force patterns, honeypot access, and successful logins
- Creates and watches a decoy file at `~/SECRET_CLASSIFIED.txt`
- Resolves public IP addresses to approximate geolocation data
- Displays a live dashboard with metrics, event tables, alerts, and a map
- Auto-refreshes every 3 seconds

## Dashboard Sections

- Hero status bar showing active monitoring targets
- Alert banners for the latest critical events
- Summary metrics for failed logins, successful logins, brute-force sources, and unique IPs
- SSH login monitor table
- Honeypot file activity table
- Attacker geolocation map
- Real-time insight feed for top failed-source IPs and monitor uptime

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

### 4. IP Geolocation

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

## Configuration Embedded in the App

The current implementation uses fixed values defined in code:

- Auth log path: `/var/log/auth.log`
- Honeypot file: `~/SECRET_CLASSIFIED.txt`
- Refresh interval: `3000 ms`
- Brute-force threshold: `5` failures
- Brute-force window: `5 minutes`
- Auth log tail size: `500` lines
- Max alert history: `8`
- Max honeypot events stored: `50`

## Current Limitations

- The log parser expects a specific auth log format and may not match all Linux distributions
- The regex currently targets `sshd-session[...]` log lines, so systems with different SSH log prefixes may produce fewer matches
- The app depends on `/var/log/auth.log`, which is not present on every Linux setup
- Geolocation requires outbound HTTP access and depends on a third-party service
- There is no persistence layer; data is kept in Streamlit session state during runtime
- There are no automated tests yet
- The project is a single-file application, so configuration and UI logic are tightly coupled

