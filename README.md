# குரல் AI — Expressive Tamil Audiobook Generator

**Multi-voice, emotion-aware Tamil text-to-speech**  
No training · No paid APIs · Runs on a laptop

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)](https://python.org)
[![TTS](https://img.shields.io/badge/TTS-Edge--TTS-orange)](https://github.com/rany2/edge-tts)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Cost](https://img.shields.io/badge/Cost-Zero-brightgreen)](https://github.com/verycareful/KuralAI)

---

## What is Kural AI?

Kural AI transforms Tamil text into expressive, multi-voice audiobooks. Paste a Tamil story with dialogue and narration, and Kural AI will:

1. **Detect dialogue vs. narration** using regex-based NLP (Tamil quote patterns, attribution verbs)
2. **Assign distinct voices** to each character (8 neural voices across India, Sri Lanka, Malaysia & Singapore)
3. **Detect emotion** from Tamil keywords and punctuation (happy, sad, angry, fear, surprise, tender)
4. **Adjust pacing** based on emotion (slower for sadness, faster for anger/excitement)
5. **Generate a stitched audiobook** with natural pauses between speaker changes

All of this runs **locally**, uses **zero paid services**, and requires **no model training**.

## Demo

> Paste Tamil text → Hit Generate → Hear multi-voice, emotion-aware audio

The web interface shows a color-coded breakdown of each detected segment — which speaker was assigned, what emotion was detected, and why — making the system fully **explainable**.

## Voice Cast (8 Neural Voices Across 4 Regions)

Users can select their preferred **Narrator Voice** from the UI, and the remaining voices dynamically form the dialogue character pool (supporting up to 7 distinct character voices):

| Voice | Region | Gender | Accent / Locale |
|---|---|---|---|
| `ta-IN-PallaviNeural` | India | Female | Indian Tamil (Default Narrator) |
| `ta-IN-ValluvarNeural` | India | Male | Indian Tamil |
| `ta-LK-KumarNeural` | Sri Lanka | Male | Sri Lankan Tamil |
| `ta-LK-SaranyaNeural` | Sri Lanka | Female | Sri Lankan Tamil |
| `ta-MY-KaniNeural` | Malaysia | Female | Malaysian Tamil |
| `ta-MY-SuryaNeural` | Malaysia | Male | Malaysian Tamil |
| `ta-SG-AnbuNeural` | Singapore | Male | Singaporean Tamil |
| `ta-SG-VenbaNeural` | Singapore | Female | Singaporean Tamil |

## Emotion Detection

Kural AI detects **9 emotion states** using a combination of Tamil keyword matching and punctuation analysis:

| Emotion | TTS Rate | Trigger Examples |
|---|---|---|
| Neutral | +0% | Default (no keywords or punctuation) |
| Excited | +10% | `!` punctuation |
| Question | +5% | `?` punctuation |
| Sad | -15% | சோகம், கண்ணீர், வருத்தம், துன்பம், வேதனை, இழப்பு, கவலை... |
| Angry | +15% | கோபம், சினம், ஆத்திரம், சீற்றம், வெறுப்பு, ரௌத்திரம்... |
| Happy | +5% | மகிழ்ச்சி, சந்தோஷம், ஆனந்தம், உற்சாகம், களிப்பு... |
| Fear | +8% | பயம், அச்சம், திகில், பீதி, நடுக்கம், பதற்றம்... |
| Surprise | +12% | ஆச்சரியம், வியப்பு, அதிசயம், அற்புதம், திகைப்பு... |
| Tender | -8% | அன்பு, காதல், பாசம், நேசம், அரவணைப்பு, ஆறுதல்... |

The vocabulary draws from the **Navarasa** (nine classical emotions) tradition and modern Tamil usage, totalling **65+ keywords** across 6 categories.

## Quick Start

### Prerequisites

- Python 3.12+
- FFmpeg (for audio stitching)

### Install

```bash
# Clone the repo
git clone https://github.com/verycareful/KuralAI.git
cd KuralAI

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

### Test the pipeline directly

```bash
python test_sample.py
```

This runs the tagger + pipeline on a sample Tamil paragraph and generates an MP3 in the `output/` directory.

## Architecture

```
Browser (index.html)
    │
    ├── POST /generate  ──→  tagger.py (regex NLP)
    │                            │
    │                            ▼
    │                        pipeline.py
    │                            │
    │                     ┌──────┼──────┐
    │                     ▼      ▼      ▼
    │                  edge-tts calls (per segment)
    │                     │      │      │
    │                     └──────┼──────┘
    │                            ▼
    │                     pydub stitching
    │                     (450ms speaker-change pauses)
    │                            │
    │                            ▼
    └── audio_url ◄──── output/<id>.mp3
```

## Project Structure

```
├── app.py              # Flask server — API endpoints
├── tagger.py           # Regex NLP — dialogue/narration, speakers, emotion
├── pipeline.py         # edge-tts synthesis + pydub audio stitching
├── examples.py         # 8 curated Tamil example passages
├── test_sample.py      # Standalone pipeline test
├── requirements.txt    # Python dependencies
├── static/
│   └── index.html      # Single-page frontend (vanilla HTML/CSS/JS)
├── .github/
│   └── workflows/
│       └── ci.yml      # GitHub Actions — test + deploy to Pages
└── output/             # Generated MP3s (gitignored)
```

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| TTS | [edge-tts](https://github.com/rany2/edge-tts) | Free Microsoft neural voices, no API key, 4 Tamil voices |
| Audio | [pydub](https://github.com/jiaaro/pydub) + FFmpeg | Simple audio manipulation, segment stitching |
| NLP | Pure Python `re` | Zero dependencies, no GPU, instant, explainable |
| Backend | [Flask](https://flask.palletsprojects.com/) | Minimal, well-known, easy to demo |
| Frontend | Vanilla HTML/CSS/JS | No build step, no framework overhead |

## Known Limitations & Future Work

### Current limitations (by design for hackathon scope)
- **Speaker attribution is heuristic** — round-robin with simple attribution verb detection, not true character-name recognition
- **Emotion detection is keyword-based** — not a trained sentiment classifier, but intentionally explainable
- **Synchronous processing** — works well for demo-length text, would need a job queue for long documents

### Future directions
- LLM-based tagging for character-name recognition and context-aware emotion
- Prosody control (pitch + volume, not just rate) once edge-tts supports it
- Batch processing and async job queue for book-length texts
- SSML generation for finer-grained speech control
- On-device deployment (edge-tts works offline with cached voices)

## Team

**KuralAI** — Problem Statement 3

## License

[MIT](LICENSE)
