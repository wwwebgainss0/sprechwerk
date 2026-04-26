# Sprechwerk — Produkt-Plan

**Status:** Ideation (2026-04-26) · **NexusHub:** `sprechwerk` (SPRW) · `e536033f-e6df-4b38-9092-81cefba76b58`
**Foundation:** `C:\Users\wwweb\ptt-whisper\ptt.py` (lokales Push-to-Talk mit Faster-Whisper auf RTX 4080)
**Codename:** *Sprechwerk* (alternativ: *DiktatGPU*, *VoiceForge*, *OffMic*, *Tüpfler*, *PTT.AI*) — endgültiger Name TBD.

---

## 1. Markt & Konkurrenz (gründlich)

| Tool | Hosting | STT-Backend | Plattformen | Hotkey | Sprachen | LLM-Polish | Vocab | Snippets | Voice-Cmds | Pricing | DSGVO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Voicely** (DE) | EU-Cloud (Frankfurt) + Privacy-Mode lokal nur Pro | "EU LLM" (intransparent) | Win, Mac | `Strg+Win` / `fn` | 50+ | ja (Cleanup, Punctuation) | ja | ja | – | Free 5k W/Mo · Pro 12€/Mo · Ent 15€/Mo | ✅ |
| **Wispr Flow** (US) | US-Cloud (kein lokal) | nicht offengelegt | Win, Mac, iOS, Android | konfigurierbar | 100+ | ja (auto-edit, ton-pass) | ja (auto-lernend) | ja | – | 14d trial · Pro ~15$/Mo · Ent SOC2/HIPAA | ❌ (US) |
| **Superwhisper** (US/INT) | Lokal (Apple Silicon) + Cloud-API | Whisper + custom AI-Modes | Mac, Win, iOS | `Opt+Space` | 100+ | ja (eigene Prompts pro Mode) | ja | – | – | Free (basic) · Pro 849$/**Jahr** · Ent | teilw. |
| **MacWhisper** (DE/INT, Goodsnooze) | Lokal + Cloud | Whisper + OpenAI/Groq | Mac only | konfigurierbar | viele | ja (mit BYOK) | ja | – | – | Pro ~50€ einmalig · Sub-Variante | teilw. |
| **Whispering / Epicenter** (OSS) | Lokal + BYOK Cloud | Whisper + Groq + Deepgram | Win, Mac, Linux | konfigurierbar | viele | ja | ja | – | – | MIT Open Source · 0€ | ✅ |
| **Linguatec Voice Pro** (DE) | 100% lokal | proprietär | Win | konfigurierbar | DE first | – | ja | ja | ja | Einmalkauf ~150€ | ✅ |
| **Nuance Dragon Professional** (US/Microsoft) | Lokal | proprietär (Legacy) | Win, Mac (eingeschr.) | konfigurierbar | DE+ | begrenzt | ja (Training) | ja | ja | 500–700€ einmalig · Med/Legal teurer | teilw. |
| **Aiko** (App-Store) | Lokal | Whisper | Mac, iOS | drag&drop | 100 | – | – | – | – | 0€ | ✅ |
| **Buzz** (OSS) | Lokal + OpenAI-API | Whisper | Win, Mac, Linux | – | viele | – | – | – | – | MIT 0€ | ✅ |
| **Sprechwerk** (uns) | 100% lokal (GPU) + opt. Cloud-Polish | **Faster-Whisper large-v3-turbo CUDA fp16** (top-tier) | Win (Mac später) | konfigurierbar | DE first, multi-lang auto | optional via Ollama lokal (Gemma/Mistral) | ja | ja | ja | Free Self-Hosted · Cloud-Hosted ~5–7€/Mo · Pro/Ent | ✅✅ |

**Marktlücken die wir füllen:**
1. **DSGVO + GPU-Genauigkeit zugleich** — Voicely macht DSGVO aber das Modell ist intransparent; wir liefern bewiesene `large-v3-turbo`.
2. **LLM-Polish 100% lokal via Ollama** — niemand sonst macht das (Voicely Cloud, Wispr Cloud, Superwhisper teilw. lokal aber kein Ollama).
3. **Workroom-/Tool-Integration** (Web-Apps, Terminals, Editor-Endpoints via HTTP-Bridge) — einzigartig.
4. **Preis-Disruption:** Self-Hosted Free + Hosted-Variante deutlich unter Voicely/Wispr.

Sources:
- [Voicely.de](https://www.voicely.de/)
- [Wispr Flow](https://wisprflow.ai/)
- [Superwhisper](https://superwhisper.com/)
- [Whispering OSS / Epicenter](https://github.com/braden-w/whispering)
- [Linguatec Voice Pro DE](https://www.linguatec.de/voicepro/transkription/)
- [Heise Transkriptions-Vergleich](https://www.heise.de/download/specials/Vergleich-Die-beste-Transkriptionssoftware-6176275)
- [Capterra Spracherkennung DE 2026](https://www.capterra.com.de/directory/30098/speech-recognition/software)
- [Wispr Flow vs ElevenLabs (toolkitly)](https://www.toolkitly.com/compare-ai-tools/584-591/218/wispr-flow-vs-elevenlabs)
- [HappyScribe Best EU Tools 2026](https://www.happyscribe.com/blog/best-transcription-software-in-europe)
- [Voicely vs Wispr Flow Vergleich (kiberatung.de)](https://www.kiberatung.de/blog/wispr-flow-alternative-warum-voicely-die-sicherere-wahl-ist)

---

## 2. Aktueller Tool-Stand (`ptt.py`)

**Bereits drin:**
- Faster-Whisper `large-v3-turbo`, CUDA, fp16 (RTX 4080) — Audio-Qualität-King
- Push-to-Talk Hotkey (default `Left Ctrl` — wechselbar via Config)
- Visual Matrix-Overlay (Waveform + States)
- System-Tray Toggle inkl. Mic-Release für andere Apps
- Auto-Mic-Detection (Arctis → eMeet Fallback mit Live-Signal-Test)
- VAD (Silence/Pad-ms)
- CCO-Workroom HTTP-Bridge (statt Clipboard)
- Beep-Feedback
- Auto-Enter nach Insert

**Heute (2026-04-26) neu eingebaut:**
- `~/.ptt-config.json` — User-Config-Datei (Hotkey, Modell, Sprache, Vocab, Snippets, Auto-Submit)
- `vocabulary[]` → Whisper `initial_prompt` für Eigennamen ("CleverDent", "EasyOrder" usw.)
- `voice_commands` → " komma ", " punkt ", " neue zeile ", " absatz ", DE+EN
- `snippets` → ganze Aussprüche als Trigger ("briefkopf" → komplette Anrede)
- `language: "auto"` → Whisper auto-detect, Tag im Log
- `auto_submit` toggleable

**Noch offen — Quick-Wins (1–2 Tage):**
- Hotkey wechseln zu `Ctrl+Win` (Voicely-Pattern, weniger False-Fires)
- Settings-UI (kleines Tk oder Web-UI via local Flask)
- Stats (Wörter/Tag, Zeit gespart)
- Optional Ollama-Polish-Pass (Filler-Removal, Punctuation-Repair) — toggle in Tray

**Mid-term (1–2 Wochen):**
- PyInstaller Single-EXE + Auto-Update via GitHub Releases
- Mac-Port (whisper.cpp Metal statt CUDA)
- Multi-Sprachen-Profile (Mode-Wechsel via Tray)
- API für Power-User (lokaler HTTP-Endpoint zum Diktieren)

---

## 3. Distribution & Website

### 3.1 Landing-Page Stack: Laravel 11 (klein gehalten)

```
sprechwerk.de
├── public/                  # static assets
├── resources/views/         # Blade templates pro Sprache
│   ├── home.blade.php
│   ├── pricing.blade.php
│   ├── docs.blade.php
│   └── compare/
│       ├── voicely.blade.php
│       ├── wispr-flow.blade.php
│       └── superwhisper.blade.php
├── lang/{de,en,fr,it,es}/   # i18n via Laravel `__()` helper
├── routes/web.php           # Localized prefix routes
└── config/seo.php           # zentrale SEO-Defaults
```

**Größe:** Bewusst minimal — kein Auth, keine DB-Persistierung außer Newsletter-Optin (SQLite reicht). Dependencies: Laravel + spatie/laravel-sitemap + spatie/laravel-translatable + spatie/schema-org für JSON-LD.

### 3.2 Mehrsprachigkeit (i18n)

- **Primär:** DE (Heimmarkt, USP DSGVO)
- **Sekundär:** EN (international Reichweite, App-User)
- **Tertiär:** FR, IT, ES (DACH-Nachbarn + EU)

URL-Schema: `sprechwerk.de/de/`, `sprechwerk.de/en/`, etc. — `hreflang` Tags pro Page für Google. Default-Redirect basierend auf `Accept-Language`.

Übersetzungs-Pipeline: DeepL-API für Erst-Drafts, manuelle Korrektur DE+EN, andere Sprachen Community-Review später.

### 3.3 SEO-Optimierung

**Keyword-Cluster (DE):**
- "DSGVO Spracherkennung", "lokales Diktiertool", "Wispr Flow Alternative deutsch", "Voicely Alternative", "GPU Whisper", "offline Diktat"

**Keyword-Cluster (EN):**
- "GDPR speech to text", "local dictation tool", "Wispr Flow alternative", "GPU Whisper desktop"

**On-Page-SEO Checkliste:**
- ✅ `<title>` 50–60 Zeichen, Keyword-first
- ✅ `<meta name="description">` 140–160 Zeichen
- ✅ `<meta name="keywords">` (low-priority aber für Bing)
- ✅ Open-Graph + Twitter-Cards
- ✅ JSON-LD: `SoftwareApplication`, `Organization`, `FAQPage`, `Product`
- ✅ Sitemap.xml + robots.txt + canonical pro Page
- ✅ hreflang-Tags pro Sprache + x-default
- ✅ Lighthouse-Score 95+ (LCP < 1.5s; statisches Blade ohne JS-Frameworks)
- ✅ Core Web Vitals — keine Webfonts blockierend, WebP-Hero-Images
- ✅ Comparison-Pages ("Sprechwerk vs Voicely") — long-tail-SEO Goldmine
- ✅ Blog-Sektion mit Diktat-Tipps, Whisper-Tutorials, DSGVO-Erklärung

**Off-Page:**
- Submit auf Product Hunt, Hacker News, t3n Pioneers, OMR, GitHub-Trending
- Backlinks via Vergleichs-Posts (Reddit r/selfhosted, r/MachineLearning, r/LocalLLaMA)
- Open-Source-Repo bringt automatische Backlinks

### 3.4 Pricing-Modell

| Tier | Preis | Was drin |
|---|---|---|
| **Self-Hosted** | 0€ | Open-Source (MIT), eigener PC + GPU, Community-Support, alle Features |
| **Cloud-Hosted Standard** | 5€/Mo · 49€/Jahr | Hosted-Modelle (du brauchst keine GPU), Auto-Updates, Settings-Sync, eMail-Support |
| **Pro** | 9€/Mo · 89€/Jahr | + LLM-Polish, Snippet-Sync, Custom-Voice-Profile, Stats |
| **Team** | 12€/User/Mo | + Shared Vocabulary, Admin-Panel, SSO |
| **On-Premise/Custom** | Anfrage | Eigener Server, Compliance-Audit, SLA |

**Disruption:** Voicely Pro 12€ → unser **Cloud-Standard 5€** schlägt deren Free-Tier (5k Wörter Limit) und unterbietet Pro um >50%. Self-Hosted ist 0€, was Wispr/Voicely strukturell nicht anbieten können.

---

## 4. Build-Reihenfolge

**Phase 1: Tool-Polish (Diese Woche)**
1. ✅ User-Config (`~/.ptt-config.json`)
2. ✅ Vocabulary, Voice-Commands, Snippets, Auto-Lang
3. ⏳ Hotkey-Wechsel default → `Ctrl+Win`
4. ⏳ Optional Ollama-Polish (lokal)
5. ⏳ Settings-UI (Tray → "Settings öffnen" → kleines Tk-Window)

**Phase 2: Distribution (Nächste Woche)**
6. ⏳ PyInstaller-Build → `Sprechwerk-Setup.exe` Single-File
7. ⏳ GitHub-Repo `sprechwerk/sprechwerk` (MIT) — Code + Releases + Issues
8. ⏳ Auto-Update via GitHub Releases JSON-Manifest
9. ⏳ Code-Signing (notwendig für SmartScreen-Trust → 100€/Jahr Cert)

**Phase 3: Website (Woche 3)**
10. ⏳ Laravel 11 Init + Blade-Templates für 5 Pages × 3 Sprachen (DE/EN + 1 Tertiär)
11. ⏳ Newsletter-Optin (Pre-Launch-Liste)
12. ⏳ SEO-Setup: sitemap, hreflang, JSON-LD, Open-Graph
13. ⏳ Comparison-Pages (Voicely, Wispr Flow, Dragon, Superwhisper)
14. ⏳ Deploy auf Plesk (DE-Server) + Cloudflare-CDN

**Phase 4: Launch (Woche 4)**
15. ⏳ Product Hunt + HN + Reddit + t3n Pre-Launch-Push
16. ⏳ Cloud-Hosted-Backend (kleiner FastAPI/Laravel-Service mit Whisper-Pool auf GPU-Server)
17. ⏳ Stripe-Integration für Paid-Tiers

**Phase 5: Mac-Port (Monat 2)**
18. ⏳ Port auf macOS via whisper.cpp + Metal — selbe Settings-File-Struktur

---

## 5. Risiken & Mitigations

| Risiko | Mitigation |
|---|---|
| User braucht GPU für large-v3-turbo lokal | Cloud-Hosted-Tier abdeckt das; CPU-Fallback mit base-v3 dokumentiert |
| Code-Signing-Cost hoch | EV-Cert via SSL.com / Sectigo (~150–300€/Jahr); ohne Signing SmartScreen-Warnung |
| Marktüberlauf — wie differenzieren? | DACH-DSGVO-First + GPU-Accuracy + Tool-Integration (CCO/Workroom) |
| Chrome blockiert globalen Hotkey im Browser | Wir liefern in System-Layer (keyboard pkg), nicht Browser-Extension — kein Konflikt |
| Whisper hat keine native deutsche Eigennamens-Erkennung | Bereits gelöst via `initial_prompt` Vokabular-Liste |
| Antivirus erkennt PyInstaller-EXE als Malware | Code-Sign + SmartScreen-Reputation aufbauen + alternativ Nuitka-Build |

---

## 6. NexusHub-Integration

- **Company:** `sprechwerk` (SPRW) registered 2026-04-26
- **Vertical:** `voice-ai`
- **Type:** `product` (vs internal/agency/b2b_client)
- **Brand-Color:** `#00ff41` (Matrix-Green, identisch mit Overlay)
- **Domain (geplant):** `sprechwerk.de`
- **CEO-Agent:** TBD — kann später ein Nexus-Agent assigned werden für Auto-Operations
- **Auto-Operations:** false (manuell-betrieben bis Launch)

Tasks/Issues unter Prefix `SPRW-XXX` anlegbar via NexusHub task-System.

---

## 7. Status nach autonomer Build-Session 2026-04-26

### Was läuft jetzt
- ✅ **NexusHub-Firma**: `sprechwerk` (SPRW) angelegt, Metadata aktualisiert
- ✅ **`ptt.py` erweitert**: Config-File, Vocabulary, Voice-Commands, Snippets, Auto-Lang, Hotkey-Default `ctrl+windows`. Backup unter `ptt.py.bak-pre-voicely`
- ✅ **Domain-WHOIS-Check**: `sprechwerk.de` und `.com` sind belegt → **Entscheidung: `sprechwerk.eu`** (frei, passt zur DSGVO-EU-Story). Backup-Optionen: `sprechwerk.io`, `sprechwerk.ai`, `diktatgpu.de`, `offmic.de`, `tuepfler.de`, `dictatum.de`, `tippsa.de` — alle frei
- ✅ **Laravel-Landing**: gescaffoldet in `~/sprechwerk-landing` (WSL Ubuntu), Laravel 12, 78 Files
  - 4 Sprachen: DE/EN/FR/IT (`lang/{xx}/site.php`)
  - 18 Routes alle 200 OK lokal
  - Pages: home, pricing, docs, faq, download
  - 5 Comparison-Pages: Voicely, Wispr Flow, Superwhisper, Dragon, MacWhisper
  - SEO: per-locale titles/descriptions, hreflang-Tags, canonical, Open-Graph, Twitter-Card, JSON-LD `SoftwareApplication`-Schema mit allen Pricing-Tiers, sitemap.xml (40 URLs), robots.txt
  - Matrix-Green Design (`#00ff41` matching Overlay)
  - Dev-Server lokal: `http://127.0.0.1:9991`
- ✅ **Git-Repo lokal initialisiert**: `~/sprechwerk-landing/.git` mit 2 Commits

### Action-Items für Cem (interaktiv nötig)

| # | Task | Cost | Wer |
|---|---|---|---|
| 1 | `gh auth login` ausführen | 0€ | Cem (interaktiv) |
| 2 | GitHub-Org `sprechwerk` anlegen + Repos `sprechwerk` (PTT-Tool) + `sprechwerk-landing` pushen | 0€ | Cem |
| 3 | Domain `sprechwerk.eu` kaufen (netcup ~10€/Jahr) | 10€/J | Cem (Bezahlung) |
| 4 | Plesk-Subscription für `sprechwerk.eu` anlegen ODER Cloudflare Pages-Deploy für statisches Output (`php artisan optimize`) | 0–5€/Mo | Cem |
| 5 | Code-Signing-Cert (SSL.com EV ~150€/Jahr) — sonst SmartScreen-Warnung beim EXE | 150€/J | Cem |
| 6 | Stripe-Account einrichten für Paid-Tiers | 0€ + 1.5%/Tx | Cem |
| 7 | **Naming-Bestätigung** — `Sprechwerk` ok? Oder lieber `OffMic` / `Diktatum` / etc.? | – | Cem |
| 8 | Hotkey final: `ctrl+windows` (jetzt) oder anderes? Im Config-File `~/.ptt-config.json` änderbar | – | Cem |

### Was du sofort tun kannst (5 Min)

```powershell
# Test ptt.py mit neuen Features
& "$env:USERPROFILE\ptt-whisper\Scripts\python.exe" "$env:USERPROFILE\ptt-whisper\ptt.py"
# Erstmaliger Start erzeugt ~/.ptt-config.json — anpassen, neu starten

# Landing-Page anschauen
# Browser → http://127.0.0.1:9991/de
# (läuft im WSL Hintergrund auf Port 9991)
```

### Phase-2-Build vorgesehen für nächste Session

- PyInstaller Single-File-EXE
- GitHub-Actions-Workflow für Auto-Build + Release
- Tray-Settings-UI (Tk-Window)
- Optional Ollama-Polish toggle
- Imprint + Privacy-Pages mit echten Cem-Daten
- Plesk/Cloudflare Deployment-Setup
- Stripe-Webhook-Endpoint im Laravel
