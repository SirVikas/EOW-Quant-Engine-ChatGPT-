"""
EOW Quant Engine — One-Click Launcher
Run:  python run.py            → paper mode, auto-opens dashboard
      python run.py live       → live mode
      python run.py --no-open  → skip browser open

What this does:
  1. Checks/starts Redis (if installed locally)
  2. Starts the FastAPI engine via uvicorn (subprocess)
  3. Waits until the engine is healthy
  4. Opens dashboard.html in the default browser
"""
import os
import sys
import time
import signal
import subprocess
import threading
import webbrowser
import urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
HOST        = "0.0.0.0"
PORT        = 8000
HEALTH_URL  = f"http://127.0.0.1:{PORT}/api/status"
DASHBOARD_URL = f"http://127.0.0.1:{PORT}"
MAX_WAIT    = 30          # seconds to wait for engine to be ready
RELOAD      = "--reload" in sys.argv

# Determine mode
MODE = "LIVE" if "live" in [a.lower() for a in sys.argv] else "PAPER"
OPEN_BROWSER = "--no-open" not in sys.argv

os.environ["TRADE_MODE"] = MODE

# ── ANSI colors ───────────────────────────────────────────────────────────────
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
R  = "\033[91m"   # red
C  = "\033[96m"   # cyan
B  = "\033[94m"   # blue
NC = "\033[0m"    # reset


def banner():
    print(f"""
{C}╔══════════════════════════════════════════════════════╗
║          EOW QUANT ENGINE  —  v1.0                   ║
║          Self-Evolving Multi-Asset Trading System     ║
╚══════════════════════════════════════════════════════╝{NC}
  Mode      : {G if MODE == 'PAPER' else R}{MODE}{NC}
  API       : {C}http://127.0.0.1:{PORT}{NC}
  Dashboard : {C}http://127.0.0.1:{PORT}{NC}
""")


def check_redis():
    """Ping Redis via REDIS_URL first; fall back to redis-cli/server if needed."""
    try:
        from core.redis_client import get_redis

        client = get_redis(timeout=5.0)
        if client.ping():
            print(f"  {G}●{NC} Redis      : connected")
            return
    except ImportError:
        print(f"  {Y}●{NC} Redis      : python client missing — install with `pip install redis`")
    except Exception:
        pass

    # Fallback probe using redis-cli when present.
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True, text=True, timeout=5,
        )
        if result.stdout.strip() == "PONG":
            print(f"  {G}●{NC} Redis      : running")
            return
    except FileNotFoundError:
        print(f"  {Y}●{NC} Redis      : not reachable at REDIS_URL — engine will use in-memory cache")
        return

    print(f"  {Y}●{NC} Redis      : not running — starting…", end="", flush=True)
    try:
        cfg_file = Path("/etc/redis/redis.conf")
        cmd = ["redis-server", str(cfg_file)] if cfg_file.exists() else ["redis-server", "--daemonize", "yes"]
        subprocess.run(cmd, capture_output=True, timeout=5)
        for _ in range(6):
            time.sleep(0.5)
            try:
                from core.redis_client import get_redis

                if get_redis(timeout=5.0).ping():
                    print(f"\r  {G}●{NC} Redis      : started successfully          ")
                    return
            except Exception:
                pass
        print(f"\r  {Y}●{NC} Redis      : started but not yet responding — continuing")
    except Exception as exc:
        print(f"\r  {Y}●{NC} Redis      : could not start ({exc}) — engine will use in-memory cache")


def wait_for_engine() -> bool:
    """Poll health endpoint until engine is ready."""
    print(f"  {Y}●{NC} Engine     : starting", end="", flush=True)
    for _ in range(MAX_WAIT * 2):
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as r:
                if r.status == 200:
                    print(f"\r  {G}●{NC} Engine     : ready{' ' * 10}")
                    return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(0.5)
    print(f"\r  {R}●{NC} Engine     : failed to start")
    return False


def open_dashboard():
    """Open the dashboard in the default browser via the engine's HTTP server."""
    time.sleep(0.5)
    url = DASHBOARD_URL
    print(f"  {G}●{NC} Dashboard  : opening browser → {url}")
    webbrowser.open(url)


def print_api_routes():
    routes = [
        ("GET",  "/api/status",   "Engine health & mode"),
        ("GET",  "/api/pnl",      "Pure PnL stats & equity curve"),
        ("GET",  "/api/market",   "Live market snapshot"),
        ("GET",  "/api/positions","Open positions & risk state"),
        ("GET",  "/api/genome",   "Genome evolution log & active DNA"),
        ("GET",  "/api/regime",   "Market regime per symbol"),
        ("GET",  "/api/thoughts", "CT-Scan AI thought log"),
        ("GET",  "/api/health",   "Self-heal watchdog status"),
        ("POST", "/api/mode/PAPER","Switch to Paper mode"),
        ("POST", "/api/mode/LIVE", "Switch to Live mode"),
        ("POST", "/api/export",   "Export full JSON state"),
        ("POST", "/api/emergency-close","Close all positions"),
        ("WS",   "/ws",           "Real-time dashboard feed"),
    ]
    print(f"\n{B}  API Endpoints:{NC}")
    for method, path, desc in routes:
        m_color = G if method == "GET" else (Y if method == "POST" else C)
        print(f"    {m_color}{method:4}{NC}  {path:30} {desc}")
    print()


def print_boot_status():
    """
    Fetch boot diagnostics from the engine and print the FTD-REF-MASTER-001
    standard status block.
    """
    import json as _json
    def _fetch():
        with urllib.request.urlopen(
            f"http://127.0.0.1:{PORT}/api/boot-status", timeout=3
        ) as r:
            return _json.loads(r.read())

    try:
        # Boot races are common: engine endpoint responds before Redis/WS settle.
        # Poll briefly so console status reflects real runtime state instead of a
        # transient CONNECTING/DISCONNECTED snapshot.
        data = None
        for _ in range(8):  # ~8 seconds max warm-up window
            data = _fetch()
            ws = data.get("websocket", "UNKNOWN")
            if ws in {"CONNECTED", "STABLE", "RECONNECTING"}:
                break
            time.sleep(1)
        if data is None:
            data = _fetch()

        def tk(cond):
            return f"{G}✅{NC}" if cond else f"{R}❌{NC}"

        redis   = data.get("redis",           "UNKNOWN")
        ws      = data.get("websocket",       "UNKNOWN")
        ind     = data.get("indicators",      "UNKNOWN")
        api     = data.get("api",             "UNKNOWN")
        strat   = data.get("strategy_engine", "UNKNOWN")
        risk    = data.get("risk_engine",     "UNKNOWN")
        mode    = data.get("execution_mode",  "UNKNOWN")
        deploy  = data.get("deployability",   "UNKNOWN")
        d_score = data.get("deployability_score", 0)

        print(f"\n{B}  Boot Status:{NC}")
        print(
            f"    Redis: {C}{redis}{NC} {tk(redis=='CONNECTED')}  |  "
            f"WebSocket: {C}{ws}{NC} {tk(ws=='CONNECTED' or ws=='STABLE')}  |  "
            f"Indicators: {C}{ind}{NC} {tk(ind in ('VALIDATED', 'WARMING_UP'))}"
        )
        print(
            f"    Strategy Engine: {C}{strat}{NC} {tk(strat=='ACTIVE')}  |  "
            f"Risk Engine: {C}{risk}{NC} {tk(risk=='ACTIVE')}  |  "
            f"Execution Mode: {C}{mode}{NC}"
        )
        print(
            f"    API: {C}{api}{NC} {tk(data.get('api_ok'))}  |  "
            f"Deployability: {C}{deploy}{NC} "
            f"({G if d_score>=85 else Y if d_score>=60 else R}{d_score:.0f}/100{NC})\n"
        )
    except Exception:
        pass   # non-critical — engine already started


def auto_inject_dna():
    """Silently inject optimized DNA on every startup."""
    import json, urllib.request
    dna_path = str(Path(__file__).parent / "data" / "exports" / "optimized_dna.json")
    if not Path(dna_path).exists():
        return
    try:
        body = json.dumps({"path": dna_path}).encode()
        req  = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/api/import-dna",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            if r.status == 200:
                print(f"  {G}●{NC} DNA         : optimized parameters loaded")
    except Exception:
        pass   # non-critical — engine runs with defaults if this fails



def main():
    banner()

    print(f"{B}  System Checks:{NC}")
    check_redis()

    # ── Start uvicorn in subprocess ───────────────────────────────────────────
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", HOST,
        "--port", str(PORT),
        "--log-level", "warning",   # keep console clean; logs go to loguru
    ]
    if RELOAD:
        cmd.append("--reload")

    proc = subprocess.Popen(cmd, cwd=str(Path(__file__).parent))

    # ── Graceful shutdown ────────────────────────────────────────────────────
    def shutdown(sig, frame):
        print(f"\n{Y}  Shutting down…{NC}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"  {G}Done.{NC}")
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── Wait + open browser ───────────────────────────────────────────────────
    if wait_for_engine():
        print_boot_status()        # FTD-REF-019 standard boot status line
        print_api_routes()
        auto_inject_dna()          # inject optimized DNA silently
        if OPEN_BROWSER:
            threading.Thread(target=open_dashboard, daemon=True).start()
        print(f"{G}  Engine is live. Press Ctrl+C to stop.{NC}\n")
    else:
        print(f"{R}  Engine failed to start. Check logs above.{NC}")
        proc.terminate()
        sys.exit(1)

    # ── Keep alive ────────────────────────────────────────────────────────────
    proc.wait()


if __name__ == "__main__":
    main()
