# Cognitive Voice Editor

**AI-powered automatic voice cleaner** for long raw recordings with retakes, mumbling, silence, and out-of-script speech.

Turns a ~50-minute messy voice-over into a tight, natural-sounding track with one command.

## Features

| Module | What it does |
|--------|----------------|
| **01 Ingestion + VAD** | Streaming load, Silero VAD, word-level Whisper timestamps (no drift) |
| **02 Cognitive Pruning** | Gemini Flash removes retakes / mumbles / fillers and assigns gravity scores |
| **03 Dynamic Pacing** | Pause length based on sentence weight + speaking momentum (not fixed ms) |
| **04 Acoustic Welding** | Zero-crossing snaps, room-tone synthesis, breath ducking, equal-power crossfades |

## Quick Start (Python)

```bash
pip install -r requirements.txt

# Get free Gemini key: https://aistudio.google.com/apikey

python run_full_pipeline.py -i your_raw.wav -l ur --api_key YOUR_KEY
```

Output: `your_raw_clean.wav`

### Options

| Flag | Description |
|------|-------------|
| `-i / --input` | Raw audio (WAV/MP3/M4A/…) |
| `-o / --output` | Clean WAV path |
| `-l / --language` | `en`, `ur`, `hi`, `ar` (omit = auto) |
| `--api_key` | Gemini API key |
| `--model_size` | `tiny` / `base` / `small` / `medium` |
| `--dry_run_prune` | Skip Gemini (no retake removal) |

## Windows EXE (GitHub Actions)

1. Open **Actions** tab on this repo  
2. Select **Build Windows EXE**  
3. Click **Run workflow**  
4. Download the artifact `CognitiveVoiceEditor-Windows` when finished  

> Note: The EXE is large (includes PyTorch + Whisper). First run will still download the speech model.

## Requirements

- Python 3.10+
- FFmpeg on PATH
- ~3 GB disk for packages + models
- Optional: free [Gemini API key](https://aistudio.google.com/apikey) for retake/mumble removal

## License

MIT – use freely.
