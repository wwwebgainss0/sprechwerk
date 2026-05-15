# sprechwerk – Push-to-Talk System

## Was ist sprechwerk?
sprechwerk ist ein Push-to-Talk (PTT) System für professionelle Audio-Workflows. Es ermöglicht die Steuerung der Mikrofonaufnahme per Tastendruck – ideal für Sprecher, Podcaster, Voice-Over-Artists und Live-Streaming.

## Sprache
- Dokumentation: Deutsch
- Code, Commits, Variablen: English

## Architektur

### Komponenten
| Komponente | Technologie | Zweck |
|------------|-------------|-------|
| **Core Script** | Python 3.x (`ptt.py`) | Hauptlogik: Tastaturhook, Audio-Routing, Mikrofonsteuerung |
| **Silent Launcher** | VBScript (`ptt-silent.vbs`) | Windows: Startet ptt.py ohne sichtbares Console-Fenster |
| **Audio Backend** | pyaudio / sounddevice | Low-Level Mikrofonsteuerung |
| **Keyboard Hook** | pynput / keyboard | Globale Tastaturabfrage |

### Ablauf