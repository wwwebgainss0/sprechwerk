"""
Push-to-Talk with Faster-Whisper + Visual Overlay + System Tray
Hold Left Ctrl to record, release to transcribe + type + Enter
System Tray icon to toggle on/off
"""

import sys
import time
import json
import re
import threading
from pathlib import Path
import numpy as np
import sounddevice as sd
import keyboard
import tkinter as tk
import ctypes
import math
from PIL import Image, ImageDraw
import pystray

# ── Global enable/disable state ──────────────────────────
ptt_enabled = True
tray_icon = None

# ── User-overridable config ────────────────────────────────
# Loaded from ~/.ptt-config.json if present. Created on first run with the
# defaults below so the user has something to edit.
CONFIG_PATH = Path.home() / ".ptt-config.json"
DEFAULT_CONFIG = {
    "model": "large-v3-turbo",
    "language": "de",         # "auto" → Whisper auto-detects per utterance
    "device": "cuda",
    "compute_type": "float16",
    "hotkey": "ctrl+windows", # was "left ctrl" — Ctrl+Win mirrors Voicely, far fewer false fires
    "voice_commands": True,   # apply " komma " → "," etc.
    "vocabulary": [           # rare proper nouns Whisper trips on
        "CleverDent", "EasyOrder", "AwesGO", "Voicely",
        "Tailscale", "macmini", "Orchestrator"
    ],
    "snippets": {             # voice trigger → expansion
        "briefkopf": "Sehr geehrte Damen und Herren,\n\n",
        "mit freundlichen gruessen": "Mit freundlichen Grüßen\nCem Acar"
    },
    "auto_submit": True       # press Enter after typing (current behaviour)
}

def _load_config():
    if CONFIG_PATH.exists():
        try:
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **user}
        except Exception as e:
            print(f"[CFG] {CONFIG_PATH} unreadable, using defaults: {e}")
    else:
        try:
            CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[CFG] wrote default config to {CONFIG_PATH}")
        except Exception as e:
            print(f"[CFG] could not seed config: {e}")
    return dict(DEFAULT_CONFIG)

CFG = _load_config()
MODEL = CFG["model"]
LANGUAGE = None if CFG["language"] == "auto" else CFG["language"]
DEVICE = CFG["device"]
COMPUTE_TYPE = CFG["compute_type"]
SAMPLE_RATE = 16000
HOTKEY = CFG["hotkey"]
INPUT_DEVICE = None  # None = system default; set index to force specific mic
VOCAB_PROMPT = ", ".join(CFG.get("vocabulary", [])) or None

# Auto-detect best microphone: Arctis Headset preferred (if live signal), eMeet Webcam as fallback
def _detect_mic():
    import sounddevice as _sd
    _emeet = None
    _arctis = None
    for _i, _d in enumerate(_sd.query_devices()):
        if _d['max_input_channels'] > 0:
            _name = _d['name'].lower()
            if 'emeet' in _name and _emeet is None:
                _emeet = _i
            elif 'arctis' in _name and _arctis is None:
                _arctis = _i
    # Test if Arctis actually delivers signal (headset might be off)
    if _arctis is not None:
        try:
            _test = _sd.rec(int(0.3 * 16000), samplerate=16000, channels=1, dtype='float32', device=_arctis)
            _sd.wait()
            if float(np.abs(_test).max()) > 0.001:
                print(f"[MIC] Arctis Headset (device {_arctis}) — active signal")
                return _arctis
            else:
                print(f"[MIC] Arctis Headset (device {_arctis}) — no signal, skipping")
        except:
            pass
    if _emeet is not None:
        print(f"[MIC] eMeet Webcam (device {_emeet}) — fallback")
        return _emeet
    print("[MIC] Using system default")
    return None

try:
    INPUT_DEVICE = _detect_mic()
except:
    pass

# ── Post-processing: voice-commands + snippet expansion ────
# Runs on the raw Whisper output before clipboard/HTTP delivery.
# Keep regex German-first; English variants added pragmatically as needed.
_VOICE_COMMANDS = [
    (re.compile(r"\s+komma\s*", re.I), ", "),
    (re.compile(r"\s+punkt\s*", re.I), ". "),
    (re.compile(r"\s+fragezeichen\s*", re.I), "? "),
    (re.compile(r"\s+ausrufezeichen\s*", re.I), "! "),
    (re.compile(r"\s+doppelpunkt\s*", re.I), ": "),
    (re.compile(r"\s+strichpunkt\s*", re.I), "; "),
    (re.compile(r"\s+(neue zeile|zeilenumbruch)\s*", re.I), "\n"),
    (re.compile(r"\s+(neuer absatz|absatz)\s*", re.I), "\n\n"),
    (re.compile(r"\s+gedankenstrich\s*", re.I), " – "),
    (re.compile(r"\s+klammer auf\s*", re.I), " ("),
    (re.compile(r"\s+klammer zu\s*", re.I), ") "),
    (re.compile(r"\s+(comma|coma)\s*", re.I), ", "),
    (re.compile(r"\s+(period|full stop)\s*", re.I), ". "),
    (re.compile(r"\s+(new line|newline)\s*", re.I), "\n"),
    (re.compile(r"\s+(new paragraph|paragraph)\s*", re.I), "\n\n"),
]
_SNIPPETS = CFG.get("snippets") or {}

def _apply_voice_commands(text: str) -> str:
    if not CFG.get("voice_commands", True):
        return text
    for pat, repl in _VOICE_COMMANDS:
        text = pat.sub(repl, text)
    text = re.sub(r" +", " ", text)          # collapse double-spaces from substitutions
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)  # tighten trailing punct
    return text.strip()

def _expand_snippets(text: str) -> str:
    # Whole-utterance trigger: "briefkopf" alone → expansion. Substring triggers
    # are too risky (fires inside normal speech).
    key = text.lower().strip().rstrip(".,!?")
    if key in _SNIPPETS:
        return _SNIPPETS[key]
    return text

def _post_process(text: str) -> str:
    if not text:
        return text
    text = _expand_snippets(text)
    text = _apply_voice_commands(text)
    return text

# ── DPI Awareness for sharp rendering ──────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# ── Overlay GUI ─────────────────────────────────────────────
class Overlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.configure(bg="#0a0a0a")

        # Size and position
        self.width = 280
        self.height = 48
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - self.width) // 2
        y = screen_h - self.height - 60
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        # Canvas for waveform + text
        self.canvas = tk.Canvas(
            self.root, width=self.width, height=self.height,
            bg="#0a0a0a", highlightthickness=0, bd=0
        )
        self.canvas.pack()

        # State
        self.state = "idle"  # idle, loading, recording, transcribing, done, error
        self.audio_level = 0.0
        self.level_history = [0.0] * 40
        self.pulse_phase = 0
        self.dot_phase = 0
        self.fade_alpha = 0.0
        self.visible = False
        self.hide_timer = None

        # Dragging
        self._drag_x = 0
        self._drag_y = 0
        self.canvas.bind("<Button-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # Start hidden
        self.root.withdraw()

        # Animation loop
        self._animate()

    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _on_drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def show(self):
        if not self.visible:
            self.root.deiconify()
            self.visible = True
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
            self.hide_timer = None

    def hide_delayed(self, ms=2000):
        if self.hide_timer:
            self.root.after_cancel(self.hide_timer)
        self.hide_timer = self.root.after(ms, self._do_hide)

    def _do_hide(self):
        self.root.withdraw()
        self.visible = False
        self.hide_timer = None

    def set_state(self, state):
        self.state = state
        if state in ("recording", "transcribing", "loading"):
            self.show()
        elif state in ("done", "error"):
            self.show()
            self.hide_delayed(2500)
        elif state == "idle":
            self.hide_delayed(1000)

    def set_audio_level(self, level):
        self.audio_level = min(level * 3, 1.0)
        self.level_history.append(self.audio_level)
        self.level_history = self.level_history[-40:]

    def _animate(self):
        self.canvas.delete("all")
        w, h = self.width, self.height
        self.pulse_phase += 0.08
        self.dot_phase += 0.15

        # Matrix green palette
        mg = "#00ff41"       # bright matrix green
        md = "#0a3d0a"       # dark green
        mm = "#00cc33"       # medium green
        ml = "#00ff4180"     # light/dim

        if self.state == "loading":
            # Falling characters effect
            self.canvas.create_text(
                w // 2, h // 2, text="\u25B8 loading model",
                fill="#005a15", font=("Consolas", 10), anchor="center"
            )
            for i in range(3):
                v = int(40 + 60 * abs(math.sin(self.dot_phase + i * 0.9)))
                color = f"#00{v:02x}10"
                cx = w // 2 + 68 + i * 10
                self.canvas.create_text(cx, h // 2, text=".", fill=color, font=("Consolas", 12, "bold"))

        elif self.state == "recording":
            # Small pulsing dot
            pulse = 0.5 + 0.5 * math.sin(self.pulse_phase * 3)
            gv = int(180 * pulse + 40)
            dot_color = f"#00{gv:02x}20"
            self.canvas.create_oval(10, h // 2 - 5, 20, h // 2 + 5, fill=dot_color, outline="#003a10")

            # Waveform bars — thin, matrix green
            bar_w = 2
            gap = 2
            start_x = 30
            for i, level in enumerate(self.level_history):
                bar_h = max(1, level * (h - 12))
                x = start_x + i * (bar_w + gap)
                if x > w - 10:
                    break
                y_top = h // 2 - bar_h // 2
                y_bot = h // 2 + bar_h // 2
                brightness = int(min(80 + level * 175, 255))
                color = f"#00{brightness:02x}20"
                self.canvas.create_rectangle(x, y_top, x + bar_w, y_bot, fill=color, outline="")

        elif self.state == "transcribing":
            # Scrolling matrix dots
            self.canvas.create_text(
                14, h // 2, text="\u25B8",
                fill="#005a15", font=("Consolas", 10), anchor="w"
            )
            self.canvas.create_text(
                28, h // 2, text="decoding",
                fill="#008a22", font=("Consolas", 10), anchor="w"
            )
            for i in range(5):
                v = int(40 + 80 * abs(math.sin(self.dot_phase * 2.5 + i * 0.7)))
                color = f"#00{v:02x}10"
                cx = 110 + i * 12
                char = chr(0x30A0 + int((self.dot_phase * 3 + i * 7) % 96))  # katakana
                self.canvas.create_text(cx, h // 2, text=char, fill=color, font=("Consolas", 9))

        elif self.state == "done":
            self.canvas.create_text(
                14, h // 2, text="\u25B8",
                fill=mm, font=("Consolas", 10), anchor="w"
            )
            self.canvas.create_text(
                28, h // 2, text="sent",
                fill=mm, font=("Consolas", 10), anchor="w"
            )

        elif self.state == "error":
            self.canvas.create_text(
                14, h // 2, text="\u25B8",
                fill="#005a15", font=("Consolas", 10), anchor="w"
            )
            self.canvas.create_text(
                28, h // 2, text="no input",
                fill="#005a15", font=("Consolas", 10), anchor="w"
            )

        # Subtle top/bottom line
        if self.state == "recording":
            gv = int(80 + 40 * math.sin(self.pulse_phase * 2))
            line_color = f"#00{gv:02x}15"
            self.canvas.create_rectangle(0, 0, w, 1, fill=line_color, outline="")
            self.canvas.create_rectangle(0, h - 1, w, h, fill=line_color, outline="")
        elif self.state != "idle":
            self.canvas.create_rectangle(0, 0, w, 1, fill="#0a2a0a", outline="")
            self.canvas.create_rectangle(0, h - 1, w, h, fill="#0a2a0a", outline="")

        self.root.after(33, self._animate)  # ~30fps

    def run(self):
        self.root.mainloop()


# ── Create overlay (must be in main thread) ─────────────────
overlay = Overlay()

# ── Load model in background ────────────────────────────────
model = None

def load_model():
    global model
    overlay.set_state("loading")
    print(f"[*] Loading Whisper model '{MODEL}' on {DEVICE}...")
    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("[OK] Model loaded! Hold Left Ctrl to speak.\n")
    overlay.set_state("idle")
    _start_stream()
    print("[OK] Mic stream active — zero latency recording ready.\n")
    try:
        import winsound
        winsound.Beep(800, 150)
    except:
        pass

threading.Thread(target=load_model, daemon=True).start()

# ── CCO Workroom HTTP bridge ────────────────────────────────
# When the active Windows foreground window is the CCO Workroom (Chrome
# tab titled "Claude Orchestrator - Workroom"), deliver the transcribed
# text via HTTP POST to the CCO server instead of clipboard+Ctrl+V.
# HTTP is immune to focus races, clipboard lockouts, and xterm's key
# handlers. Falls back to the clipboard path for any other window.
CCO_URL = "http://localhost:8787"
_CCO_TITLE_MARKERS = ("Claude Orchestrator - Workroom", "Workroom - Claude")

def _foreground_window_title() -> str:
    """Return the Windows foreground-window title, or '' on any error."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or ""
    except Exception:
        return ""

def _cco_workroom_is_active() -> bool:
    title = _foreground_window_title()
    return any(marker in title for marker in _CCO_TITLE_MARKERS)

def _dictate_to_cco(text: str) -> bool:
    """POST text to CCO's dictate endpoint; return True on 2xx."""
    try:
        import urllib.request, urllib.error, json as _json
        body = _json.dumps({"text": text, "submit": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{CCO_URL}/api/workroom/dictate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            return 200 <= r.status < 300
    except Exception as e:
        print(f"[CCO] dictate failed, falling back: {e}")
        return False

# ── Type text via clipboard ─────────────────────────────────
def type_text(text):
    # Preferred path: HTTP bridge when the user is in the CCO Workroom.
    # Skips clipboard + Ctrl+V + focus races entirely.
    if _cco_workroom_is_active():
        if _dictate_to_cco(text):
            return

    import subprocess
    # Use CREATE_NO_WINDOW to prevent PowerShell flash
    CREATE_NO_WINDOW = 0x08000000
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"Add-Type -AssemblyName System.Windows.Forms; "
         f"[System.Windows.Forms.Clipboard]::SetText('{text.replace(chr(39), chr(39)+chr(39))}')"],
        capture_output=True, timeout=5,
        creationflags=CREATE_NO_WINDOW,
    )
    time.sleep(0.4)
    keyboard.press('ctrl')
    keyboard.press('v')
    keyboard.release('v')
    keyboard.release('ctrl')
    time.sleep(0.5)
    keyboard.press_and_release('enter')

# ── Recording state ─────────────────────────────────────────
recording = False
audio_chunks = []
stream = None

def _audio_callback(indata, frames, time_info, status):
    if recording:
        audio_chunks.append(indata.copy())
        level = float(np.abs(indata).mean())
        overlay.set_audio_level(level)

def _start_stream():
    global stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32',
        callback=_audio_callback,
        blocksize=512,
        latency='low',
        device=INPUT_DEVICE,
    )
    stream.start()

def start_recording():
    global recording, audio_chunks
    if recording or model is None or not ptt_enabled:
        return
    audio_chunks = []
    recording = True
    overlay.set_state("recording")
    try:
        import winsound
        winsound.Beep(1200, 80)
    except:
        pass
    print("  [REC] Recording...")

def stop_recording():
    global recording
    if not recording:
        return
    recording = False

    if not audio_chunks:
        overlay.set_state("idle")
        return

    audio = np.concatenate(audio_chunks, axis=0).flatten()
    duration = len(audio) / SAMPLE_RATE

    if duration < 0.3:
        print("  (too short)")
        overlay.set_state("idle")
        return

    overlay.set_state("transcribing")
    print(f"  [*] Transcribing {duration:.1f}s...")
    start = time.time()

    try:
        segments, info = model.transcribe(
            audio,
            language=LANGUAGE,
            beam_size=5,
            initial_prompt=VOCAB_PROMPT,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        text = _post_process(text)
        elapsed = time.time() - start

        if text:
            lang_tag = f" [{getattr(info, 'language', '?')}]" if LANGUAGE is None else ""
            print(f"  [OK] [{elapsed:.1f}s]{lang_tag} \"{text}\"")
            overlay.set_state("done")
            type_text(text)
        else:
            print(f"  [--] [{elapsed:.1f}s] (no speech)")
            overlay.set_state("error")

    except Exception as e:
        print(f"  [ERR] {e}")
        overlay.set_state("error")

# ── System Tray Icon ─────────────────────────────────────
def _create_tray_icon(color):
    """Create a small mic icon with given color."""
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Mic body
    draw.rounded_rectangle([20, 8, 44, 38], radius=8, fill=color)
    # Mic stand
    draw.arc([16, 24, 48, 52], start=0, end=180, fill=color, width=3)
    draw.line([32, 52, 32, 60], fill=color, width=3)
    draw.line([22, 60, 42, 60], fill=color, width=3)
    return img

def _toggle_ptt(icon, item):
    global ptt_enabled, stream
    ptt_enabled = not ptt_enabled
    _update_tray_icon()
    state = "AN" if ptt_enabled else "AUS"
    print(f"  [TRAY] Push-to-Talk: {state}")
    overlay.set_state("done" if ptt_enabled else "error")

    if not ptt_enabled:
        # Release mic completely so other apps (CS2 etc.) can use it
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except:
                pass
            stream = None
        print("  [TRAY] Mic freigegeben")
    else:
        # Re-acquire mic when re-enabling
        if model is not None and stream is None:
            _start_stream()
            print("  [TRAY] Mic stream reaktiviert")

def _update_tray_icon():
    global tray_icon
    if tray_icon is None:
        return
    if ptt_enabled:
        tray_icon.icon = _create_tray_icon((0, 204, 51))
        tray_icon.title = "PTT: AN (Left Ctrl)"
    else:
        tray_icon.icon = _create_tray_icon((180, 30, 30))
        tray_icon.title = "PTT: AUS"

def _quit_app(icon, item):
    icon.stop()
    overlay.root.quit()
    sys.exit(0)

def _run_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: "Ausschalten" if ptt_enabled else "Einschalten",
            _toggle_ptt,
            default=True,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", _quit_app),
    )
    tray_icon = pystray.Icon(
        "ptt-whisper",
        _create_tray_icon((0, 204, 51)),
        "PTT: AN (Left Ctrl)",
        menu,
    )
    tray_icon.run()

# ── Hotkey handling ─────────────────────────────────────
print("=" * 50)
print("  PUSH-TO-TALK (Faster-Whisper + RTX 4080)")
print("=" * 50)
print(f"  Hotkey:    Hold {HOTKEY.upper()}")
print(f"  Model:     {MODEL}")
print(f"  Language:  {LANGUAGE}")
print(f"  Device:    {DEVICE} ({COMPUTE_TYPE})")
print(f"  Tray:      Mic-Icon neben der Uhr (Klick = Ein/Aus)")
print("=" * 50)
print()

keyboard.on_press_key(HOTKEY, lambda e: start_recording(), suppress=False)
keyboard.on_release_key(HOTKEY, lambda e: threading.Thread(target=stop_recording, daemon=True).start(), suppress=False)

# Start tray icon in background thread
threading.Thread(target=_run_tray, daemon=True).start()

print("Waiting for input...\n")

# Run overlay mainloop (blocks main thread)
overlay.run()
