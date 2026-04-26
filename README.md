# Sprechwerk

> Lokales DSGVO-Diktiertool für Windows & Mac. Faster-Whisper auf deiner GPU. Keine Cloud, kein Abo.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![GPU](https://img.shields.io/badge/GPU-CUDA%20%2F%20Apple%20Silicon-orange.svg)]()

**Sprechwerk** ist ein Push-to-Talk-Diktiertool, das `Faster-Whisper large-v3-turbo` mit CUDA `fp16` auf deiner GPU nutzt — komplett offline. Du hältst einen Hotkey, sprichst, lässt los — der Text landet im fokussierten Textfeld jeder App.

DSGVO-konforme Alternative zu [Voicely](https://www.voicely.de/), [Wispr Flow](https://wisprflow.ai/), [Superwhisper](https://superwhisper.com/) und [Nuance Dragon](https://www.nuance.com/dragon.html). Open Source unter MIT-Lizenz.

## Features

- 🎙️ **Push-to-Talk** mit Hotkey `Ctrl+Win` (konfigurierbar)
- 🚀 **GPU-beschleunigt** — Sub-Sekunden-Transkription auf RTX/Apple Silicon
- 🔒 **100% lokal** — Audio verlässt nie dein Gerät
- 🌍 **100+ Sprachen** mit Auto-Detection
- 📝 **Custom Vocabulary** für Eigennamen und Fachbegriffe
- ⚡ **Voice-Commands** — `"komma"`, `"punkt"`, `"neue zeile"`, …
- 📋 **Snippets** — Voice-Trigger für ganze Textbausteine
- 🎨 **Matrix-Overlay** — Live-Waveform + Status
- 🛠️ **Tray-Icon** — Mic für andere Apps freigeben
- 🔌 **HTTP-Bridge** — direkte Integration in Web-Apps (z.B. Claude Code Orchestrator Workroom)

## Quick Start

```powershell
# Voraussetzungen: Python 3.12+, CUDA-fähige NVIDIA GPU
git clone https://github.com/wwwebgainss0/sprechwerk
cd sprechwerk
python -m venv .
Scripts\pip install faster-whisper sounddevice keyboard pillow pystray numpy
Scripts\python ptt.py
```

Bei erstem Start wird `~/.ptt-config.json` automatisch angelegt — anpassen, neu starten.

## Konfiguration

```json
{
  "model": "large-v3-turbo",
  "language": "auto",
  "device": "cuda",
  "compute_type": "float16",
  "hotkey": "ctrl+windows",
  "voice_commands": true,
  "vocabulary": ["DeineEigennamen", "Fachbegriffe"],
  "snippets": {"briefkopf": "Sehr geehrte Damen und Herren,\n\n"},
  "auto_submit": true
}
```

## Voice-Commands

| Sage | Wird zu |
|---|---|
| `komma` / `comma` | `,` |
| `punkt` / `period` | `.` |
| `fragezeichen` | `?` |
| `neue zeile` / `new line` | `\n` |
| `absatz` / `paragraph` | `\n\n` |
| `klammer auf` / `klammer zu` | `(` / `)` |

## Vergleich zur Konkurrenz

Siehe [PRODUCT.md](PRODUCT.md) für detaillierten Vergleich gegen Voicely, Wispr Flow, Superwhisper, MacWhisper, Linguatec Voice Pro, Nuance Dragon.

## Landing-Page

[github.com/wwwebgainss0/sprechwerk-landing](https://github.com/wwwebgainss0/sprechwerk-landing) — Laravel-Site in DE/EN/FR/IT mit SEO + JSON-LD + Comparison-Pages.

## License

MIT © 2026 Sprechwerk. Audio-Daten gehören dir und bleiben bei dir.
