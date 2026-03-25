import html
import ipaddress
import os
import queue
import re
import shutil
import socket
import subprocess
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


st.set_page_config(
    page_title="SecureScope",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

:root {
    --bg: #07131a;
    --bg-alt: #0e2125;
    --panel: rgba(6, 19, 27, 0.84);
    --panel-border: rgba(90, 186, 169, 0.26);
    --text: #d8efe8;
    --muted: #8db1a8;
    --cyan: #72f6e6;
    --amber: #ffb84d;
    --red: #ff6b6b;
    --green: #7ff2b0;
}

html, body, [class*="css"], .stApp {
    background:
        radial-gradient(circle at top left, rgba(114, 246, 230, 0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(255, 184, 77, 0.12), transparent 24%),
        linear-gradient(180deg, #041015 0%, #07131a 55%, #0a1416 100%);
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
}

#MainMenu, header, footer { visibility: hidden; }
.block-container { padding: 1.1rem 1.4rem 1.8rem 1.4rem !important; max-width: 100% !important; }

.hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(114, 246, 230, 0.18);
    border-radius: 20px;
    padding: 1.3rem 1.4rem 1.1rem;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, rgba(9, 26, 36, 0.92), rgba(14, 33, 37, 0.86));
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
}

.hero::after {
    content: "";
    position: absolute;
    inset: auto -20% -45% auto;
    width: 340px;
    height: 340px;
    background: radial-gradient(circle, rgba(255, 184, 77, 0.16), transparent 62%);
}

.hero h1 {
    margin: 0;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 2.4rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--cyan);
}

.hero-sub {
    margin-top: 0.35rem;
    color: var(--muted);
    font-size: 0.88rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.hero-status {
    display: inline-flex;
    gap: 0.5rem;
    align-items: center;
    margin-top: 0.95rem;
    border: 1px solid rgba(127, 242, 176, 0.2);
    border-radius: 999px;
    padding: 0.3rem 0.7rem;
    background: rgba(127, 242, 176, 0.07);
    color: #b7f8d0;
    font-size: 0.82rem;
}

.hero-status-dot {
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 16px rgba(127, 242, 176, 0.7);
    animation: pulse 1.9s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.55; transform: scale(0.88); }
}

.alert-banner {
    border: 1px solid rgba(255, 107, 107, 0.28);
    background: linear-gradient(90deg, rgba(76, 17, 17, 0.95), rgba(124, 25, 25, 0.8));
    color: #ffd2d2;
    border-radius: 14px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.7rem;
    font-size: 0.9rem;
    animation: siren 1.8s infinite;
}

@keyframes siren {
    0%, 100% { box-shadow: 0 0 0 rgba(255, 107, 107, 0); }
    50% { box-shadow: 0 0 22px rgba(255, 107, 107, 0.2); }
}

.panel {
    border-radius: 18px;
    border: 1px solid var(--panel-border);
    background: var(--panel);
    backdrop-filter: blur(18px);
    padding: 1rem 1rem 1.1rem;
    min-height: 100%;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}

.panel-title {
    margin-bottom: 0.85rem;
    color: var(--cyan);
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
}

.metrics {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.7rem;
    margin-bottom: 1rem;
}

.metric {
    border-radius: 14px;
    border: 1px solid rgba(141, 177, 168, 0.16);
    background: rgba(255, 255, 255, 0.025);
    padding: 0.8rem;
}

.metric-value {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 1.6rem;
    line-height: 1;
}

.metric-label {
    margin-top: 0.3rem;
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.metric-danger { color: var(--red); }
.metric-warn { color: var(--amber); }
.metric-good { color: var(--green); }
.metric-cyan { color: var(--cyan); }

.section-title {
    margin: 1.35rem 0 0.8rem;
    color: #b9f5ea;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.88rem;
}

.table-wrap {
    max-height: 350px;
    overflow-y: auto;
    border: 1px solid rgba(141, 177, 168, 0.12);
    border-radius: 14px;
}

.log-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}

.log-table th {
    position: sticky;
    top: 0;
    background: #10242a;
    color: #b2d7ce;
    text-align: left;
    padding: 0.75rem 0.7rem;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.log-table td {
    padding: 0.7rem;
    border-top: 1px solid rgba(141, 177, 168, 0.08);
    color: var(--text);
    vertical-align: top;
}

.log-table tr:hover td {
    background: rgba(114, 246, 230, 0.04);
}

.badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.18rem 0.55rem;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.badge-failed { background: rgba(255, 107, 107, 0.12); color: #ff9f9f; }
.badge-success { background: rgba(127, 242, 176, 0.12); color: #9ef8c3; }
.badge-invalid { background: rgba(255, 184, 77, 0.12); color: #ffd08a; }
.badge-honey { background: rgba(114, 246, 230, 0.12); color: #a1f7ec; }
.badge-brute { background: rgba(255, 107, 107, 0.18); color: #ffd2d2; }

.pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 0.8rem;
}

.pill {
    border-radius: 999px;
    border: 1px solid rgba(255, 184, 77, 0.24);
    background: rgba(255, 184, 77, 0.08);
    color: #ffd08a;
    padding: 0.35rem 0.7rem;
    font-size: 0.76rem;
}

.subtle {
    color: var(--muted);
    font-size: 0.82rem;
}

.empty {
    border: 1px dashed rgba(141, 177, 168, 0.18);
    border-radius: 14px;
    padding: 1.3rem;
    color: var(--muted);
    text-align: center;
}
</style>
""",
    unsafe_allow_html=True,
)


AUTH_LOG = Path("/var/log/auth.log")
HONEYPOT_FILE = Path.home() / "SECRET_CLASSIFIED.txt"
TSHARK_BIN = shutil.which("tshark")
NETWORK_INTERFACE = "any"
REFRESH_INTERVAL_MS = 3000
BRUTE_THRESHOLD = 5
BRUTE_WINDOW = timedelta(minutes=5)
MAX_AUTH_LINES = 500
MAX_ALERTS = 8
MAX_HONEY_EVENTS = 50
MAX_PACKET_EVENTS = 1200
PACKET_RETENTION = timedelta(minutes=10)
PACKET_WINDOW = timedelta(minutes=1)
PORT_SCAN_THRESHOLD = 10
SYN_BURST_THRESHOLD = 40
SSH_PACKET_THRESHOLD = 15
ICMP_SPIKE_THRESHOLD = 25
GLOBAL_PACKET_SPIKE_THRESHOLD = 250
GEO_TIMEOUT = 3


LOG_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+\S+\s+sshd-session\[\d+\]:\s+(?P<message>.*)$"
)
FAILED_RE = re.compile(
    r"Failed password for (?P<user>\S+) from (?P<ip>[0-9a-fA-F:\.]+) port (?P<port>\d+)"
)
ACCEPT_RE = re.compile(
    r"Accepted (?P<method>password|publickey) for (?P<user>\S+) from (?P<ip>[0-9a-fA-F:\.]+) port (?P<port>\d+)"
)
INVALID_RE = re.compile(
    r"Invalid user (?P<user>\S+) from (?P<ip>[0-9a-fA-F:\.]+) port (?P<port>\d+)"
)


def ensure_state() -> None:
    defaults = {
        "honeypot_events": [],
        "packet_events": [],
        "alerts": [],
        "observer_started": False,
        "observer_ref": None,
        "honeypot_queue": queue.Queue(),
        "packet_queue": queue.Queue(),
        "seen_honeypot_event_keys": set(),
        "seen_alert_keys": set(),
        "geo_cache": {},
        "packet_capture_started": False,
        "packet_capture_process": None,
        "packet_capture_thread": None,
        "packet_capture_error": None,
        "packet_capture_status": "idle",
        "packet_capture_started_at": None,
        "local_ips": set(),
        "monitor_started_at": time.time(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def ensure_honeypot() -> None:
    if HONEYPOT_FILE.exists():
        return

    HONEYPOT_FILE.write_text(
        "\n".join(
            [
                "=== CLASSIFIED: INTERNAL NETWORK ACCESS TOKENS ===",
                "vpn_gateway=10.0.0.12",
                "prod_ssh_user=ops-admin",
                "service_account=backup-bot",
                "api_token=sk-prod-redacted-placeholder",
                "rotation_schedule=every-6-hours",
                "=== END FILE ===",
                "",
            ]
        ),
        encoding="utf-8",
    )


class HoneypotHandler(FileSystemEventHandler):
    def __init__(self, honeypot_path: Path, event_queue: queue.Queue) -> None:
        self.honeypot_path = honeypot_path.resolve()
        self.event_queue = event_queue

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return

        src_path = Path(event.src_path).resolve()
        if src_path != self.honeypot_path:
            return

        event_time = datetime.now()
        event_key = f"{event.event_type}:{int(event_time.timestamp())}:{src_path}"
        self.event_queue.put(
            {
                "event_key": event_key,
                "timestamp": event_time,
                "time_label": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": event.event_type.upper(),
                "path": str(src_path),
                "user": os.environ.get("USER", "unknown"),
            }
        )


def start_observer() -> None:
    if st.session_state.observer_started:
        return

    handler = HoneypotHandler(HONEYPOT_FILE, st.session_state.honeypot_queue)
    observer = Observer()
    observer.schedule(handler, str(HONEYPOT_FILE.parent), recursive=False)
    observer.daemon = True
    observer.start()
    st.session_state.observer_ref = observer
    st.session_state.observer_started = True


def detect_local_ips() -> set[str]:
    ips = {"127.0.0.1", "::1"}

    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            check=False,
        )
        for value in result.stdout.split():
            try:
                ipaddress.ip_address(value)
            except ValueError:
                continue
            ips.add(value)
    except OSError:
        pass

    try:
        for entry in socket.getaddrinfo(socket.gethostname(), None):
            value = entry[4][0]
            try:
                ipaddress.ip_address(value)
            except ValueError:
                continue
            ips.add(value)
    except socket.gaierror:
        pass

    return ips


def packet_reader_worker(process: subprocess.Popen, event_queue: queue.Queue) -> None:
    if process.stdout is None:
        return

    for raw_line in process.stdout:
        line = raw_line.strip()
        if not line:
            continue
        event_queue.put(line)


def ensure_packet_capture() -> None:
    if not st.session_state.local_ips:
        st.session_state.local_ips = detect_local_ips()

    process = st.session_state.packet_capture_process
    if process is not None and process.poll() is not None:
        stderr_output = ""
        if process.stderr is not None:
            stderr_output = process.stderr.read().strip()
        st.session_state.packet_capture_process = None
        st.session_state.packet_capture_thread = None
        st.session_state.packet_capture_started = False
        st.session_state.packet_capture_status = "error"
        st.session_state.packet_capture_error = stderr_output or "tshark exited unexpectedly"

    if st.session_state.packet_capture_started:
        st.session_state.packet_capture_status = "active"
        return

    if not TSHARK_BIN:
        st.session_state.packet_capture_status = "unavailable"
        st.session_state.packet_capture_error = "tshark is not installed on this host"
        return

    command = [
        TSHARK_BIN,
        "-i",
        NETWORK_INTERFACE,
        "-l",
        "-n",
        "-Q",
        "-f",
        "ip",
        "-T",
        "fields",
        "-E",
        "separator=|",
        "-E",
        "occurrence=f",
        "-e",
        "frame.time_epoch",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "tcp.srcport",
        "-e",
        "tcp.dstport",
        "-e",
        "udp.srcport",
        "-e",
        "udp.dstport",
        "-e",
        "ip.proto",
        "-e",
        "frame.len",
        "-e",
        "tcp.flags.syn",
        "-e",
        "tcp.flags.ack",
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        st.session_state.packet_capture_status = "error"
        st.session_state.packet_capture_error = f"Unable to start tshark: {exc}"
        return

    thread = threading.Thread(
        target=packet_reader_worker,
        args=(process, st.session_state.packet_queue),
        daemon=True,
        name="securescope-packet-reader",
    )
    thread.start()

    time.sleep(0.15)
    if process.poll() is not None:
        stderr_output = ""
        if process.stderr is not None:
            stderr_output = process.stderr.read().strip()
        st.session_state.packet_capture_status = "error"
        st.session_state.packet_capture_error = stderr_output or "tshark exited immediately"
        return

    st.session_state.packet_capture_process = process
    st.session_state.packet_capture_thread = thread
    st.session_state.packet_capture_started = True
    st.session_state.packet_capture_status = "active"
    st.session_state.packet_capture_error = None
    st.session_state.packet_capture_started_at = time.time()


def read_auth_log() -> list[str]:
    result = subprocess.run(
        ["tail", "-n", str(MAX_AUTH_LINES), str(AUTH_LOG)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()


def drain_honeypot_queue() -> None:
    while True:
        try:
            payload = st.session_state.honeypot_queue.get_nowait()
        except queue.Empty:
            break

        event_key = payload["event_key"]
        if event_key in st.session_state.seen_honeypot_event_keys:
            continue

        st.session_state.seen_honeypot_event_keys.add(event_key)
        st.session_state.honeypot_events.insert(
            0,
            {
                "timestamp": payload["timestamp"],
                "time_label": payload["time_label"],
                "event": payload["event"],
                "path": payload["path"],
                "user": payload["user"],
            },
        )
        st.session_state.honeypot_events = st.session_state.honeypot_events[:MAX_HONEY_EVENTS]
        push_alert(
            category="honeypot",
            message=f"Honeypot file {payload['event'].lower()} event on {Path(payload['path']).name}",
            dedupe_key=event_key,
        )


def parse_timestamp(raw_value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def parse_auth_events(lines: list[str]) -> list[dict]:
    events = []
    for line in lines:
        log_match = LOG_RE.match(line)
        if not log_match:
            continue

        timestamp = parse_timestamp(log_match.group("timestamp"))
        if not timestamp:
            continue

        message = log_match.group("message")
        base = {
            "timestamp": timestamp,
            "time_label": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "raw": line,
        }

        failed_match = FAILED_RE.search(message)
        if failed_match:
            events.append(
                {
                    **base,
                    "status": "FAILED",
                    "user": failed_match.group("user"),
                    "ip": failed_match.group("ip"),
                    "port": failed_match.group("port"),
                    "method": "password",
                }
            )
            continue

        accepted_match = ACCEPT_RE.search(message)
        if accepted_match:
            events.append(
                {
                    **base,
                    "status": "SUCCESS",
                    "user": accepted_match.group("user"),
                    "ip": accepted_match.group("ip"),
                    "port": accepted_match.group("port"),
                    "method": accepted_match.group("method"),
                }
            )
            continue

        invalid_match = INVALID_RE.search(message)
        if invalid_match:
            events.append(
                {
                    **base,
                    "status": "INVALID",
                    "user": invalid_match.group("user"),
                    "ip": invalid_match.group("ip"),
                    "port": invalid_match.group("port"),
                    "method": "unknown",
                }
            )

    return sorted(events, key=lambda item: item["timestamp"], reverse=True)


def detect_bruteforce(events: list[dict]) -> dict[str, dict]:
    failures_by_ip = defaultdict(list)
    for event in events:
        if event["status"] in {"FAILED", "INVALID"}:
            failures_by_ip[event["ip"]].append(event["timestamp"])

    detections = {}
    for ip, timestamps in failures_by_ip.items():
        ordered = sorted(timestamps)
        start = 0
        for end, current in enumerate(ordered):
            while current - ordered[start] > BRUTE_WINDOW:
                start += 1
            window_count = end - start + 1
            if window_count >= BRUTE_THRESHOLD:
                detections[ip] = {
                    "count": window_count,
                    "first_seen": ordered[start],
                    "last_seen": current,
                }
                break
    return detections


def push_alert(category: str, message: str, dedupe_key: str) -> None:
    if dedupe_key in st.session_state.seen_alert_keys:
        return

    st.session_state.seen_alert_keys.add(dedupe_key)
    st.session_state.alerts.insert(
        0,
        {
            "time_label": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "message": message,
        },
    )
    st.session_state.alerts = st.session_state.alerts[:MAX_ALERTS]


def protocol_label(proto_number: str) -> str:
    mapping = {
        "1": "ICMP",
        "6": "TCP",
        "17": "UDP",
        "58": "ICMPv6",
    }
    return mapping.get(proto_number, proto_number or "UNKNOWN")


def classify_direction(src_ip: str, dst_ip: str) -> str:
    local_ips = st.session_state.local_ips
    if dst_ip in local_ips and src_ip not in local_ips:
        return "INBOUND"
    if src_ip in local_ips and dst_ip not in local_ips:
        return "OUTBOUND"
    if src_ip in local_ips and dst_ip in local_ips:
        return "LOCAL"
    return "UNKNOWN"


def parse_packet_line(line: str) -> dict | None:
    fields = line.split("|")
    if len(fields) < 10:
        return None

    try:
        timestamp = datetime.fromtimestamp(float(fields[0]))
    except ValueError:
        return None

    src_ip = fields[1].strip()
    dst_ip = fields[2].strip()
    if not src_ip or not dst_ip:
        return None

    tcp_src, tcp_dst, udp_src, udp_dst = (field.strip() for field in fields[3:7])
    src_port = tcp_src or udp_src or "-"
    dst_port = tcp_dst or udp_dst or "-"
    proto_number = fields[7].strip()
    protocol = protocol_label(proto_number)

    try:
        length = int(fields[8].strip() or "0")
    except ValueError:
        length = 0

    syn_flag = fields[9].strip() == "1"
    ack_flag = fields[10].strip() == "1" if len(fields) > 10 else False
    direction = classify_direction(src_ip, dst_ip)

    return {
        "timestamp": timestamp,
        "time_label": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": protocol,
        "length": length,
        "syn": syn_flag,
        "ack": ack_flag,
        "direction": direction,
    }


def drain_packet_queue() -> None:
    while True:
        try:
            raw_line = st.session_state.packet_queue.get_nowait()
        except queue.Empty:
            break

        event = parse_packet_line(raw_line)
        if not event:
            continue
        st.session_state.packet_events.insert(0, event)

    if len(st.session_state.packet_events) > MAX_PACKET_EVENTS:
        st.session_state.packet_events = st.session_state.packet_events[:MAX_PACKET_EVENTS]


def prune_packet_events() -> None:
    cutoff = datetime.now() - PACKET_RETENTION
    st.session_state.packet_events = [
        event for event in st.session_state.packet_events if event["timestamp"] >= cutoff
    ]


def collect_resource_metrics() -> dict:
    cpu_cores = os.cpu_count() or 1
    try:
        load1, load5, _ = os.getloadavg()
        cpu_load_pct = min(100.0, (load1 / max(cpu_cores, 1)) * 100)
        load_label = f"{load1:.2f} / {load5:.2f}"
    except OSError:
        cpu_load_pct = 0.0
        load_label = "Unavailable"

    mem_total_kb = 0
    mem_available_kb = 0
    try:
        with Path("/proc/meminfo").open(encoding="utf-8") as handle:
            for line in handle:
                key, _, value = line.partition(":")
                amount = value.strip().split()[0] if value.strip() else "0"
                if key == "MemTotal":
                    mem_total_kb = int(amount)
                elif key == "MemAvailable":
                    mem_available_kb = int(amount)
    except (OSError, ValueError):
        mem_total_kb = 0
        mem_available_kb = 0

    if mem_total_kb:
        mem_used_pct = ((mem_total_kb - mem_available_kb) / mem_total_kb) * 100
        mem_label = f"{(mem_total_kb - mem_available_kb) / 1024 / 1024:.1f} GB"
    else:
        mem_used_pct = 0.0
        mem_label = "Unavailable"

    disk_total, disk_used, _ = shutil.disk_usage(Path.home())
    disk_used_pct = (disk_used / disk_total) * 100 if disk_total else 0.0

    return {
        "cpu_load_pct": cpu_load_pct,
        "load_label": load_label,
        "memory_used_pct": mem_used_pct,
        "memory_label": mem_label,
        "disk_used_pct": disk_used_pct,
        "disk_label": f"{disk_used / 1024 / 1024 / 1024:.1f} GB",
        "cpu_cores": cpu_cores,
    }


def analyze_packets() -> dict:
    ensure_packet_capture()
    drain_packet_queue()
    prune_packet_events()

    now = datetime.now()
    recent_cutoff = now - PACKET_WINDOW
    recent_events = [
        event for event in st.session_state.packet_events if event["timestamp"] >= recent_cutoff
    ]
    suspicious_window = [
        event for event in recent_events if event["direction"] in {"INBOUND", "LOCAL", "UNKNOWN"}
    ]

    events_by_src = defaultdict(list)
    for event in suspicious_window:
        events_by_src[event["src_ip"]].append(event)

    anomalies = []
    for src_ip, events in events_by_src.items():
        last_seen = max(event["timestamp"] for event in events)
        distinct_ports = {event["dst_port"] for event in events if event["dst_port"] != "-"}
        syn_count = sum(
            1
            for event in events
            if event["protocol"] == "TCP" and event["syn"] and not event["ack"]
        )
        ssh_hits = sum(1 for event in events if event["dst_port"] == "22")
        icmp_hits = sum(1 for event in events if event["protocol"] in {"ICMP", "ICMPv6"})

        if len(distinct_ports) >= PORT_SCAN_THRESHOLD:
            anomalies.append(
                {
                    "severity": "HIGH",
                    "src_ip": src_ip,
                    "kind": "Port Scan",
                    "detail": f"{len(distinct_ports)} destination ports in 60s",
                    "count": len(events),
                    "last_seen": last_seen,
                }
            )

        if syn_count >= SYN_BURST_THRESHOLD:
            anomalies.append(
                {
                    "severity": "HIGH",
                    "src_ip": src_ip,
                    "kind": "SYN Burst",
                    "detail": f"{syn_count} TCP SYN packets in 60s",
                    "count": syn_count,
                    "last_seen": last_seen,
                }
            )

        if ssh_hits >= SSH_PACKET_THRESHOLD:
            anomalies.append(
                {
                    "severity": "MEDIUM",
                    "src_ip": src_ip,
                    "kind": "SSH Hammering",
                    "detail": f"{ssh_hits} packets to port 22 in 60s",
                    "count": ssh_hits,
                    "last_seen": last_seen,
                }
            )

        if icmp_hits >= ICMP_SPIKE_THRESHOLD:
            anomalies.append(
                {
                    "severity": "MEDIUM",
                    "src_ip": src_ip,
                    "kind": "ICMP Spike",
                    "detail": f"{icmp_hits} ICMP packets in 60s",
                    "count": icmp_hits,
                    "last_seen": last_seen,
                }
            )

    if len(suspicious_window) >= GLOBAL_PACKET_SPIKE_THRESHOLD:
        last_seen = max(event["timestamp"] for event in suspicious_window)
        anomalies.append(
            {
                "severity": "HIGH",
                "src_ip": "multiple",
                "kind": "Traffic Spike",
                "detail": f"{len(suspicious_window)} suspicious packets in 60s",
                "count": len(suspicious_window),
                "last_seen": last_seen,
            }
        )

    for anomaly in anomalies:
        push_alert(
            category="network",
            message=f"{anomaly['kind']} from {anomaly['src_ip']}: {anomaly['detail']}",
            dedupe_key=(
                f"network:{anomaly['kind']}:{anomaly['src_ip']}:"
                f"{anomaly['last_seen'].replace(second=0, microsecond=0).isoformat()}"
            ),
        )

    top_sources = Counter(event["src_ip"] for event in suspicious_window).most_common(8)
    top_ports = Counter(
        event["dst_port"] for event in suspicious_window if event["dst_port"] != "-"
    ).most_common(8)
    protocol_mix = Counter(event["protocol"] for event in recent_events).most_common(6)

    return {
        "recent_events": recent_events,
        "suspicious_window": suspicious_window,
        "anomalies": sorted(anomalies, key=lambda item: item["last_seen"], reverse=True),
        "top_sources": top_sources,
        "top_ports": top_ports,
        "protocol_mix": protocol_mix,
        "capture_status": st.session_state.packet_capture_status,
        "capture_error": st.session_state.packet_capture_error,
    }


def geolocate_ip(ip: str) -> dict | None:
    cached = st.session_state.geo_cache.get(ip)
    if cached is not None:
        return cached

    try:
        if ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback:
            st.session_state.geo_cache[ip] = None
            return None
    except ValueError:
        st.session_state.geo_cache[ip] = None
        return None

    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,message,country,city,lat,lon,query"},
            timeout=GEO_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        st.session_state.geo_cache[ip] = None
        return None

    if payload.get("status") != "success":
        st.session_state.geo_cache[ip] = None
        return None

    result = {
        "ip": ip,
        "country": payload.get("country", "Unknown"),
        "city": payload.get("city", "Unknown"),
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
    }
    st.session_state.geo_cache[ip] = result
    return result


def build_map_rows(events: list[dict]) -> list[dict]:
    seen = set()
    map_rows = []
    for event in events:
        ip = event["ip"]
        if ip in seen:
            continue
        seen.add(ip)
        geo = geolocate_ip(ip)
        if not geo:
            continue
        map_rows.append(
            {
                "lat": geo["lat"],
                "lon": geo["lon"],
                "ip": geo["ip"],
                "country": geo["country"],
                "city": geo["city"],
            }
        )
    return map_rows


def analyze() -> dict:
    drain_honeypot_queue()
    auth_events = parse_auth_events(read_auth_log())
    brute_force = detect_bruteforce(auth_events)
    packet_analysis = analyze_packets()

    for ip, detail in brute_force.items():
        push_alert(
            category="bruteforce",
            message=f"Brute force pattern from {ip}: {detail['count']} failures in 5 minutes",
            dedupe_key=f"brute:{ip}:{detail['last_seen'].isoformat()}",
        )

    latest_success = next((event for event in auth_events if event["status"] == "SUCCESS"), None)
    if latest_success:
        push_alert(
            category="success",
            message=f"Latest successful SSH login: {latest_success['user']} from {latest_success['ip']}",
            dedupe_key=f"success:{latest_success['timestamp'].isoformat()}:{latest_success['ip']}",
        )

    return {
        "auth_events": auth_events,
        "brute_force": brute_force,
        "map_rows": build_map_rows(auth_events),
        "packet_analysis": packet_analysis,
        "resource_metrics": collect_resource_metrics(),
    }


def badge(status: str, brute: bool = False) -> str:
    if brute:
        return '<span class="badge badge-brute">BRUTE</span>'
    if status == "SUCCESS":
        return '<span class="badge badge-success">SUCCESS</span>'
    if status == "INVALID":
        return '<span class="badge badge-invalid">INVALID</span>'
    return '<span class="badge badge-failed">FAILED</span>'


def render_auth_table(events: list[dict], brute_force: dict[str, dict]) -> None:
    if not events:
        st.markdown('<div class="empty">No SSH authentication events found in auth.log.</div>', unsafe_allow_html=True)
        return

    rows = []
    for event in events[:25]:
        is_brute = event["ip"] in brute_force and event["status"] in {"FAILED", "INVALID"}
        rows.append(
            f"""
<tr>
    <td>{html.escape(event['time_label'])}</td>
    <td>{html.escape(event['ip'])}</td>
    <td>{html.escape(event['user'])}</td>
    <td>{html.escape(event['method'])}</td>
    <td>{badge(event['status'], brute=is_brute)}</td>
</tr>
"""
        )

    st.markdown(
        f"""
<div class="table-wrap">
    <table class="log-table">
        <thead>
            <tr><th>Time</th><th>Source IP</th><th>User</th><th>Auth</th><th>Status</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
""",
        unsafe_allow_html=True,
    )


def render_honeypot_table() -> None:
    events = st.session_state.honeypot_events
    if not events:
        st.markdown(
            f'<div class="empty">Honeypot idle. Touch <code>{html.escape(str(HONEYPOT_FILE))}</code> to generate an event.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = []
    for event in events[:20]:
        rows.append(
            f"""
<tr>
    <td>{html.escape(event['time_label'])}</td>
    <td><span class="badge badge-honey">{html.escape(event['event'])}</span></td>
    <td>{html.escape(event['user'])}</td>
    <td>{html.escape(event['path'])}</td>
</tr>
"""
        )

    st.markdown(
        f"""
<div class="table-wrap">
    <table class="log-table">
        <thead>
            <tr><th>Time</th><th>Event</th><th>User</th><th>Path</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
""",
        unsafe_allow_html=True,
    )


def render_map(map_rows: list[dict]) -> None:
    if not map_rows:
        st.markdown(
            '<div class="empty">No geolocatable public IPs yet. Private addresses remain visible in the SSH table but not on the map.</div>',
            unsafe_allow_html=True,
        )
        return

    st.map(pd.DataFrame(map_rows), latitude="lat", longitude="lon", size=None, use_container_width=True)
    pills = [
        f"<div class=\"pill\">{html.escape(row['ip'])} · {html.escape(row['city'])}, {html.escape(row['country'])}</div>"
        for row in map_rows[:10]
    ]
    st.markdown(f'<div class="pill-row">{"".join(pills)}</div>', unsafe_allow_html=True)


def render_resource_panel(resource_metrics: dict) -> None:
    st.markdown(
        f"""
<div class="metrics">
    <div class="metric">
        <div class="metric-value metric-cyan">{resource_metrics['cpu_load_pct']:.0f}%</div>
        <div class="metric-label">CPU Load ({html.escape(resource_metrics['load_label'])})</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-warn">{resource_metrics['memory_used_pct']:.0f}%</div>
        <div class="metric-label">Memory Used ({html.escape(resource_metrics['memory_label'])})</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-good">{resource_metrics['disk_used_pct']:.0f}%</div>
        <div class="metric-label">Home Disk Used ({html.escape(resource_metrics['disk_label'])})</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-cyan">{resource_metrics['cpu_cores']}</div>
        <div class="metric-label">CPU Cores</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_network_anomaly_table(anomalies: list[dict], capture_status: str, capture_error: str | None) -> None:
    if capture_status != "active":
        message = capture_error or "Packet capture is not active."
        st.markdown(f'<div class="empty">{html.escape(message)}</div>', unsafe_allow_html=True)
        return

    if not anomalies:
        st.markdown(
            '<div class="empty">No packet anomalies detected in the last 60 seconds.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = []
    for anomaly in anomalies[:20]:
        severity_class = "badge-brute" if anomaly["severity"] == "HIGH" else "badge-invalid"
        rows.append(
            f"""
<tr>
    <td>{html.escape(anomaly['last_seen'].strftime("%Y-%m-%d %H:%M:%S"))}</td>
    <td><span class="badge {severity_class}">{html.escape(anomaly['severity'])}</span></td>
    <td>{html.escape(anomaly['src_ip'])}</td>
    <td>{html.escape(anomaly['kind'])}</td>
    <td>{html.escape(anomaly['detail'])}</td>
</tr>
"""
        )

    st.markdown(
        f"""
<div class="table-wrap">
    <table class="log-table">
        <thead>
            <tr><th>Time</th><th>Severity</th><th>Source IP</th><th>Type</th><th>Detail</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
""",
        unsafe_allow_html=True,
    )


def render_packet_table(packet_events: list[dict], capture_status: str, capture_error: str | None) -> None:
    if capture_status != "active":
        message = capture_error or "Packet capture is not active."
        st.markdown(f'<div class="empty">{html.escape(message)}</div>', unsafe_allow_html=True)
        return

    if not packet_events:
        st.markdown(
            '<div class="empty">Waiting for IP packets. Generate traffic from another system to populate this panel.</div>',
            unsafe_allow_html=True,
        )
        return

    rows = []
    for event in packet_events[:30]:
        rows.append(
            f"""
<tr>
    <td>{html.escape(event['time_label'])}</td>
    <td>{html.escape(event['src_ip'])}</td>
    <td>{html.escape(event['dst_ip'])}</td>
    <td>{html.escape(event['protocol'])}</td>
    <td>{html.escape(event['dst_port'])}</td>
    <td>{html.escape(event['direction'])}</td>
</tr>
"""
        )

    st.markdown(
        f"""
<div class="table-wrap">
    <table class="log-table">
        <thead>
            <tr><th>Time</th><th>Source IP</th><th>Destination IP</th><th>Protocol</th><th>Dst Port</th><th>Direction</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
</div>
""",
        unsafe_allow_html=True,
    )


def render_network_summary(packet_analysis: dict) -> None:
    recent_events = packet_analysis["recent_events"]
    suspicious_window = packet_analysis["suspicious_window"]
    anomalies = packet_analysis["anomalies"]

    st.markdown(
        f"""
<div class="metrics">
    <div class="metric">
        <div class="metric-value metric-cyan">{len(recent_events)}</div>
        <div class="metric-label">Packets Last 60s</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-danger">{len(anomalies)}</div>
        <div class="metric-label">Active Anomalies</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-warn">{len({event['src_ip'] for event in suspicious_window})}</div>
        <div class="metric-label">Active Source IPs</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-good">{packet_analysis['capture_status'].upper()}</div>
        <div class="metric-label">Capture Status</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if packet_analysis["capture_error"]:
        st.markdown(
            f'<div class="subtle">Capture issue: {html.escape(packet_analysis["capture_error"])}</div>',
            unsafe_allow_html=True,
        )


ensure_state()
ensure_honeypot()
start_observer()

analysis = analyze()
auth_events = analysis["auth_events"]
brute_force = analysis["brute_force"]
map_rows = analysis["map_rows"]
packet_analysis = analysis["packet_analysis"]
resource_metrics = analysis["resource_metrics"]

failed_count = sum(event["status"] in {"FAILED", "INVALID"} for event in auth_events)
success_count = sum(event["status"] == "SUCCESS" for event in auth_events)
brute_count = len(brute_force)
unique_source_count = len({event["ip"] for event in auth_events})
uptime = str(timedelta(seconds=int(time.time() - st.session_state.monitor_started_at)))

st.markdown(
    f"""
<div class="hero">
    <h1>SecureScope</h1>
    <div class="hero-sub">SSH login monitoring, host visibility, honeypot watch, packet anomaly detection, attacker geolocation, real-time alerts</div>
    <div class="hero-status"><span class="hero-status-dot"></span>Monitoring {html.escape(str(AUTH_LOG))}, {html.escape(HONEYPOT_FILE.name)}, and live packets on {html.escape(NETWORK_INTERFACE)}</div>
</div>
""",
    unsafe_allow_html=True,
)

for alert in st.session_state.alerts[:3]:
    st.markdown(
        f'<div class="alert-banner">[{html.escape(alert["time_label"])}] {html.escape(alert["message"])}</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">SSH And Host Monitoring</div>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="metrics">
    <div class="metric">
        <div class="metric-value metric-danger">{failed_count}</div>
        <div class="metric-label">Failed / Invalid</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-good">{success_count}</div>
        <div class="metric-label">Successful SSH</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-warn">{brute_count}</div>
        <div class="metric-label">Brute Force Sources</div>
    </div>
    <div class="metric">
        <div class="metric-value metric-cyan">{unique_source_count}</div>
        <div class="metric-label">Unique Source IPs</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

ssh_col, honey_col, resource_col = st.columns([1.15, 0.95, 0.9], gap="medium")

with ssh_col:
    st.markdown('<div class="panel"><div class="panel-title">SSH Login Monitor</div>', unsafe_allow_html=True)
    render_auth_table(auth_events, brute_force)
    if brute_force:
        brute_items = "".join(
            f'<div class="pill">{html.escape(ip)} · {detail["count"]} failures</div>'
            for ip, detail in brute_force.items()
        )
        st.markdown(f'<div class="pill-row">{brute_items}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with honey_col:
    st.markdown('<div class="panel"><div class="panel-title">Honeypot File Monitor</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtle">Watching <code>{html.escape(str(HONEYPOT_FILE))}</code></div>',
        unsafe_allow_html=True,
    )
    render_honeypot_table()
    st.markdown('</div>', unsafe_allow_html=True)

with resource_col:
    st.markdown('<div class="panel"><div class="panel-title">Host Resource Monitor</div>', unsafe_allow_html=True)
    render_resource_panel(resource_metrics)
    st.markdown(
        f"""
<div class="subtle">
    Monitor uptime: {html.escape(uptime)}<br>
    Last refresh: {html.escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}<br>
    Local IPs: <code>{html.escape(', '.join(sorted(st.session_state.local_ips)) or 'Unavailable')}</code>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

map_col, insight_col = st.columns([1.25, 0.75], gap="medium")

with map_col:
    st.markdown('<div class="panel"><div class="panel-title">Attacker Geolocation Map</div>', unsafe_allow_html=True)
    render_map(map_rows)
    st.markdown('</div>', unsafe_allow_html=True)

with insight_col:
    top_failed_ips = Counter(
        event["ip"] for event in auth_events if event["status"] in {"FAILED", "INVALID"}
    ).most_common(8)
    st.markdown('<div class="panel"><div class="panel-title">Real-Time Insight Feed</div>', unsafe_allow_html=True)
    if top_failed_ips:
        pills = "".join(
            f'<div class="pill">{html.escape(ip)} · {count} attempts</div>'
            for ip, count in top_failed_ips
        )
        st.markdown(f'<div class="pill-row">{pills}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">No failed SSH sources detected yet.</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
<div class="subtle" style="margin-top:1rem;">Correlate these IPs with the packet monitoring section below to confirm whether they are scanning, flooding, or only attempting SSH logins.</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Network Packet Monitoring</div>', unsafe_allow_html=True)

st.markdown('<div class="panel"><div class="panel-title">Packet Capture Summary</div>', unsafe_allow_html=True)
render_network_summary(packet_analysis)
if packet_analysis["top_sources"]:
    source_pills = "".join(
        f'<div class="pill">{html.escape(ip)} · {count} packets</div>'
        for ip, count in packet_analysis["top_sources"]
    )
    st.markdown(f'<div class="pill-row">{source_pills}</div>', unsafe_allow_html=True)
if packet_analysis["top_ports"]:
    port_pills = "".join(
        f'<div class="pill">Port {html.escape(port)} · {count} hits</div>'
        for port, count in packet_analysis["top_ports"]
    )
    st.markdown(f'<div class="pill-row">{port_pills}</div>', unsafe_allow_html=True)
if packet_analysis["protocol_mix"]:
    proto_pills = "".join(
        f'<div class="pill">{html.escape(proto)} · {count}</div>'
        for proto, count in packet_analysis["protocol_mix"]
    )
    st.markdown(f'<div class="pill-row">{proto_pills}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

network_left, network_right = st.columns([1, 1], gap="medium")

with network_left:
    st.markdown('<div class="panel"><div class="panel-title">Detected Packet Anomalies</div>', unsafe_allow_html=True)
    render_network_anomaly_table(
        packet_analysis["anomalies"],
        packet_analysis["capture_status"],
        packet_analysis["capture_error"],
    )
    st.markdown('</div>', unsafe_allow_html=True)

with network_right:
    st.markdown('<div class="panel"><div class="panel-title">Recent Packet Activity</div>', unsafe_allow_html=True)
    render_packet_table(
        packet_analysis["recent_events"],
        packet_analysis["capture_status"],
        packet_analysis["capture_error"],
    )
    st.markdown('</div>', unsafe_allow_html=True)

st_autorefresh(interval=REFRESH_INTERVAL_MS, key="securescope-refresh")
