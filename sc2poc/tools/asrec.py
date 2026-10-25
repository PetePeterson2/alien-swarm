"""Record an Alien Swarm play session: frames of the game window (only while it is
the foreground window), an input log, and auto-started Source demos.

Out dir layout:
  frames/NNNNNN.jpg   game client area, full res
  frames.csv          idx, t (s since start), client x,y,w,h
  input.csv           t, event, detail  (key down/up, cursor every 50 ms)
  rec.log             recorder notes (demo starts/stops)
Stops when <out>/STOP exists or swarm.exe exits.
"""
import ctypes, ctypes.wintypes as W, os, sys, time, threading, subprocess, queue, re
from concurrent.futures import ThreadPoolExecutor
from PIL import ImageGrab

ctypes.windll.shcore.SetProcessDpiAwareness(2)
u = ctypes.windll.user32
OUT = sys.argv[1]
FPS = float(sys.argv[2]) if len(sys.argv) > 2 else 20
GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Alien Swarm"
CONLOG = os.path.join(GAME, "swarm", "combat_session.log")
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
T0 = time.perf_counter()
now = lambda: time.perf_counter() - T0
stop = threading.Event()
logf = open(os.path.join(OUT, "rec.log"), "a", buffering=1)
def note(s):
    logf.write(f"{now():9.3f} {time.strftime('%H:%M:%S')} {s}\n")

def game_hwnd():
    found = []
    def cb(h, l):
        n = ctypes.create_unicode_buffer(64); u.GetWindowTextW(h, n, 64)
        c = ctypes.create_unicode_buffer(64); u.GetClassNameW(h, c, 64)
        if c.value == "Valve001" and n.value == "Alien Swarm" and u.IsWindowVisible(h):
            found.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, W.HWND, W.LPARAM)(cb), 0)
    return found[0] if found else None

def client_rect(h):
    r = W.RECT(); u.GetClientRect(h, ctypes.byref(r))
    p = W.POINT(0, 0); u.ClientToScreen(h, ctypes.byref(p))
    return p.x, p.y, r.right, r.bottom

def game_running():
    o = subprocess.run(["tasklist", "/fi", "imagename eq swarm.exe", "/nh"], capture_output=True, text=True).stdout
    return "swarm.exe" in o

state = {"hwnd": None, "fg": False, "rect": None}

def watch_window():
    while not stop.is_set():
        h = state["hwnd"]
        if not h or not u.IsWindow(h):
            h = state["hwnd"] = game_hwnd()
        state["fg"] = bool(h) and u.GetForegroundWindow() == h and not u.IsIconic(h)
        if h: state["rect"] = client_rect(h)
        time.sleep(0.1)

KEYS = {0x01: "LMB", 0x02: "RMB", 0x04: "MMB", 0x57: "W", 0x41: "A", 0x53: "S", 0x44: "D",
        0x52: "R", 0x45: "E", 0x46: "F", 0x47: "G", 0x51: "Q", 0x31: "1", 0x32: "2", 0x33: "3",
        0x34: "4", 0x10: "SHIFT", 0x20: "SPACE", 0x09: "TAB", 0x5A: "Z", 0x56: "V", 0x58: "X",
        0x78: "F9", 0x1B: "ESC"}

def watch_input():
    f = open(os.path.join(OUT, "input.csv"), "a", buffering=1)
    f.write("t,event,detail\n")
    down = {k: False for k in KEYS}
    last_cur = 0; last_fg = None
    while not stop.is_set():
        t = now(); fg = state["fg"]
        if fg != last_fg:
            f.write(f"{t:.3f},focus,{int(fg)}\n"); last_fg = fg
        if fg:
            for vk, name in KEYS.items():
                d = bool(u.GetAsyncKeyState(vk) & 0x8000)
                if d != down[vk]:
                    down[vk] = d; f.write(f"{t:.3f},{'down' if d else 'up'},{name}\n")
            if t - last_cur > 0.05 and state["rect"]:
                p = W.POINT(); u.GetCursorPos(ctypes.byref(p))
                x, y, w, h = state["rect"]
                f.write(f"{t:.3f},cur,{p.x - x} {p.y - y}\n"); last_cur = t
        time.sleep(0.005)

def hijack(cmd):
    # never let -hijack launch a fresh game
    if not game_running() or not state["hwnd"]: return
    subprocess.Popen([os.path.join(GAME, "swarm.exe"), "-hijack"] + cmd.split())

def watch_demo():
    """Start a demo whenever the game is in a map and not already recording."""
    while not state["hwnd"] and not stop.is_set(): time.sleep(1)
    hijack("+con_logfile combat_session.log")
    n = 1
    while os.path.exists(os.path.join(GAME, "swarm", f"combat{n}.dem")): n += 1
    pos = os.path.getsize(CONLOG) if os.path.exists(CONLOG) else 0
    recording = False; last_try = -99
    while not stop.is_set():
        if os.path.exists(CONLOG):
            with open(CONLOG, "r", errors="replace") as c:
                c.seek(pos); txt = c.read(); pos = c.tell()
            for line in txt.splitlines():
                if re.search(r"Recording to .*\.dem", line):
                    recording = True; note(f"demo start: {line.strip()}")
                elif re.search(r"Completed demo", line):
                    recording = False; note(f"demo end: {line.strip()}"); n += 1
                elif re.search(r"Already recording", line):
                    recording = True
        if not recording and now() - last_try > 20:
            last_try = now(); hijack(f"+record combat{n}")
        time.sleep(1)

def main():
    note(f"start, fps {FPS}")
    for fn in (watch_window, watch_input, watch_demo):
        threading.Thread(target=fn, daemon=True).start()
    pool = ThreadPoolExecutor(4)
    csv = open(os.path.join(OUT, "frames.csv"), "a", buffering=1)
    csv.write("idx,t,x,y,w,h\n")
    idx = len(os.listdir(os.path.join(OUT, "frames")))
    period = 1.0 / FPS; nxt = now(); last_check = 0
    while True:
        if os.path.exists(os.path.join(OUT, "STOP")): break
        if now() - last_check > 5:
            last_check = now()
            if not game_running(): note("game exited"); break
        if state["fg"] and state["rect"]:
            x, y, w, h = state["rect"]
            t = now()
            im = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            path = os.path.join(OUT, "frames", f"{idx:06d}.jpg")
            pool.submit(im.save, path, quality=82)
            csv.write(f"{idx},{t:.3f},{x},{y},{w},{h}\n"); idx += 1
        nxt += period
        d = nxt - now()
        if d > 0: time.sleep(d)
        else: nxt = now()
    stop.set(); pool.shutdown(wait=True)
    note(f"stop, {idx} frames")
    hijack("+stop")

main()
