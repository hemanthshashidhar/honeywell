import html
import ipaddress
import os
import queue
import re
import subprocess
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
REFRESH_INTERVAL_MS = 3000
BRUTE_THRESHOLD = 5
BRUTE_WINDOW = timedelta(minutes=5)
MAX_AUTH_LINES = 500
MAX_ALERTS = 8
MAX_HONEY_EVENTS = 50
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
        "alerts": [],
        "observer_started": False,
        "observer_ref": None,
        "honeypot_queue": queue.Queue(),
        "seen_honeypot_event_keys": set(),
        "seen_alert_keys": set(),
        "geo_cache": {},
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


ensure_state()
ensure_honeypot()
start_observer()

analysis = analyze()
auth_events = analysis["auth_events"]
brute_force = analysis["brute_force"]
map_rows = analysis["map_rows"]

failed_count = sum(event["status"] in {"FAILED", "INVALID"} for event in auth_events)
success_count = sum(event["status"] == "SUCCESS" for event in auth_events)
brute_count = len(brute_force)
unique_source_count = len({event["ip"] for event in auth_events})
uptime = str(timedelta(seconds=int(time.time() - st.session_state.monitor_started_at)))

st.markdown(
    f"""
<div class="hero">
    <h1>SecureScope</h1>
    <div class="hero-sub">SSH login monitoring, brute force detection, honeypot watch, attacker geolocation, real-time alerts</div>
    <div class="hero-status"><span class="hero-status-dot"></span>Monitoring {html.escape(str(AUTH_LOG))} and {html.escape(HONEYPOT_FILE.name)}</div>
</div>
""",
    unsafe_allow_html=True,
)

for alert in st.session_state.alerts[:3]:
    st.markdown(
        f'<div class="alert-banner">[{html.escape(alert["time_label"])}] {html.escape(alert["message"])}</div>',
        unsafe_allow_html=True,
    )

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

left_col, right_col = st.columns([1.2, 1], gap="medium")

with left_col:
    st.markdown('<div class="panel"><div class="panel-title">SSH Login Monitor</div>', unsafe_allow_html=True)
    render_auth_table(auth_events, brute_force)
    if brute_force:
        brute_items = "".join(
            f'<div class="pill">{html.escape(ip)} · {detail["count"]} failures</div>'
            for ip, detail in brute_force.items()
        )
        st.markdown(f'<div class="pill-row">{brute_items}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="panel"><div class="panel-title">Honeypot File Monitor</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtle">Watching <code>{html.escape(str(HONEYPOT_FILE))}</code></div>',
        unsafe_allow_html=True,
    )
    render_honeypot_table()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

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
<div class="subtle" style="margin-top:1rem;">
    Monitor uptime: {html.escape(uptime)}<br>
    Last refresh: {html.escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}<br>
    Active interface observed earlier: <code>wlp3s0</code>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

st_autorefresh(interval=REFRESH_INTERVAL_MS, key="securescope-refresh")
