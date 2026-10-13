"""Private per-account graphical desktops for user-operated Flow sign-in.

No Google password/cookie APIs. VNC/CDP ports remain loopback-only. HTTP access
is mediated by the authenticated server, never by a publicly exposed VNC port.
"""
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import time
from pathlib import Path


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def alive(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=.2): return True
    except OSError: return False


def ensure(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    file = root / "desktop.json"
    if file.exists():
        data = json.loads(file.read_text())
        if alive(data["websocket_port"]): return data
    for binary in ("Xvfb", "x11vnc", "websockify"):
        if not shutil.which(binary): raise ValueError("Remote browser runtime is missing " + binary + "; the setup agent must provision the container")
    display = next((i for i in range(100, 1000) if not Path(f"/tmp/.X{i}-lock").exists()), None)
    if display is None: raise ValueError("No free isolated browser display")
    rfb, ws = free_port(), free_port()
    if rfb == ws: ws = free_port()
    env = {**os.environ, "DISPLAY": ":" + str(display)}
    log = (root / "desktop.log").open("ab")
    processes = []
    try:
        p = subprocess.Popen(["Xvfb", env["DISPLAY"], "-screen", "0", "1440x900x24", "-nolisten", "tcp"],
                             env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        processes.append(p)
        for _ in range(20):
            if Path(f"/tmp/.X11-unix/X{display}").exists(): break
            time.sleep(.1)
        p = subprocess.Popen(["x11vnc", "-display", env["DISPLAY"], "-localhost", "-rfbport", str(rfb),
                              "-forever", "-shared", "-nopw", "-quiet"], env=env,
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        processes.append(p)
        p = subprocess.Popen(["websockify", "--heartbeat=30", f"127.0.0.1:{ws}", f"127.0.0.1:{rfb}"],
                             env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        processes.append(p)
        for _ in range(30):
            if alive(ws) and alive(rfb):
                data = {"display": env["DISPLAY"], "rfb_port": rfb, "websocket_port": ws,
                        "pids": [p.pid for p in processes]}
                file.write_text(json.dumps(data)); os.chmod(file, 0o600)
                return data
            time.sleep(.1)
        raise ValueError("Remote browser desktop failed to start; inspect private runtime logs")
    except Exception:
        for p in processes:
            p.terminate()
        raise
    finally:
        log.close()


def websocket_port(data_dir, account_id):
    if not re.fullmatch(r"[a-f0-9]{32}", account_id): raise ValueError("Invalid Flow account")
    data = json.loads((Path(data_dir) / "profiles" / account_id / "desktop.json").read_text())
    port = data["websocket_port"]
    if type(port) is not int or not 1024 <= port <= 65535: raise ValueError("Invalid managed desktop port")
    return port


if __name__ == "__main__":
    import sys
    print(json.dumps(ensure(sys.argv[1])))
