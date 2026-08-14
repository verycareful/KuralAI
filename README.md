# குரல் AI — Expressive Tamil Audiobook Generator

**Multi-Voice, Emotion-Aware Tamil Text-to-Speech Engine**  
Zero GPU · Zero Paid APIs · Open Source · Cloud & Local Deployment

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)](https://python.org)
[![TTS](https://img.shields.io/badge/TTS-Edge--TTS-orange)](https://github.com/rany2/edge-tts)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Cost](https://img.shields.io/badge/Cost-Zero-brightgreen)](https://github.com/verycareful/KuralAI)

---

## Overview

Kural AI transforms raw Tamil literary and conversational text into expressive, multi-character audiobooks. By combining rule-based morphological NLP, Navarasa emotion modulation, and neural speech synthesis, Kural AI provides:

1. **Dialogue vs. Narration Segmentation**: Identifies dialogue blocks using Tamil punctuation conventions (smart quotes, ASCII quotes, guillemets) and attribution verbs.
2. **Gender-Consistent Voice Mapping**: Accurately maps male characters to male voices and female characters to female voices using verb morphology (`என்றான்` vs. `என்றாள்`) and character noun analysis.
3. **Persistent Character Voice Consistency**: Tracks character names across scenes so that recurring characters retain their exact voice throughout the entire audiobook.
4. **Navarasa Emotion & Prosody Modulation**: Dynamically modulates speech rate, pitch frequency, and volume gain based on 65+ classical Navarasa keywords and punctuation.
5. **Silence & Cadence Management**: Inserts 450ms pauses on speaker transitions and 200ms pauses between same-speaker clauses for natural human conversational cadence.
6. **Plain Baseline Comparison**: Generates side-by-side comparative audio against a flat, single-voice monotone Microsoft TTS baseline.

---

## Voice Cast (8 Neural Voices Across 4 Regions)

Kural AI integrates all 8 Microsoft Neural Tamil voices across India, Sri Lanka, Malaysia, and Singapore:

| Voice Name | Region | Gender | Accent / Locale | Role Pool |
| :--- | :--- | :--- | :--- | :--- |
| `ta-IN-PallaviNeural` | India | Female | Indian Tamil | Default Narrator / Female Characters |
| `ta-IN-ValluvarNeural` | India | Male | Indian Tamil | Male Characters / Narrator |
| `ta-LK-KumarNeural` | Sri Lanka | Male | Sri Lankan Tamil | Male Characters |
| `ta-LK-SaranyaNeural` | Sri Lanka | Female | Sri Lankan Tamil | Female Characters |
| `ta-MY-KaniNeural` | Malaysia | Female | Malaysian Tamil | Female Characters |
| `ta-MY-SuryaNeural` | Malaysia | Male | Malaysian Tamil | Male Characters |
| `ta-SG-AnbuNeural` | Singapore | Male | Singaporean Tamil | Male Characters |
| `ta-SG-VenbaNeural` | Singapore | Female | Singaporean Tamil | Female Characters |

---

## Emotion & SSML Prosody Modulation

When an emotion is detected via Tamil keyword matching or punctuation analysis, the synthesis engine modulates three core acoustic parameters alongside dynamic pause insertion:

| Emotion | Speed (Rate) | Pitch (Frequency) | Volume (Gain) | Acoustic Effect & SSML Rationale |
| :--- | :---: | :---: | :---: | :--- |
| **Angry (ரௌத்திரம்)** | **`+15%`** | **`+6Hz`** | **`+15%`** | Fast, loud, tense pitch conveying high aggression and forceful projection. |
| **Sad (கருணை/சோகம்)** | **`-15%`** | **`-6Hz`** | **`-10%`** | Slow, subdued, lower pitch conveying melancholic weight and grief. |
| **Surprise (அற்புதம்)** | **`+12%`** | **`+10Hz`** | **`+10%`** | Sharp elevated pitch and tempo reflecting sudden shock and wonder. |
| **Excited / Joy (உற்சாகம்)** | **`+10%`** | **`+6Hz`** | **`+10%`** | Bright pitch and brisk tempo for exclamation and triumph. |
| **Fear (பயானகம்)** | **`+8%`** | **`+8Hz`** | **`+5%`** | High, trembling pitch and hurried pace conveying panic and anxiety. |
| **Tender / Love (சிருங்காரம்)** | **`-8%`** | **`-3Hz`** | **`-15%`** | Soft, intimate whisper-level volume with gentle, elongated delivery. |
| **Question (வினா)** | **`+5%`** | **`+5Hz`** | **`+0%`** | Rising sentence-final pitch inflection for interrogative queries. |
| **Neutral (சாந்தம்)** | **`+0%`** | **`+0Hz`** | **`+0%`** | Balanced conversational baseline for descriptive background narration. |

---

## Gender Attribution & Character Consistency Engine

The attribution engine in `tagger.py` operates on Tamil grammar and morphology:

1. **Suffix Morphological Analysis**:
   - **Female verbs** (`-ஆள்`): `என்றாள்`, `கேட்டாள்`, `சொன்னாள்`, `கூறினாள்`, `அலறினாள்`, `முணுமுணுத்தாள்`...
   - **Male verbs** (`-ஆன்`): `என்றான்`, `கேட்டான்`, `சொன்னான்`, `கூறினான்`, `அலறினான்`, `முணுமுணுத்தான்`...
2. **Context Window Scanning**:
   - Scans 80 characters preceding and following each quote to extract character nouns (`முருகன்`, `செல்வம்`, `வசந்தா`, `லட்சுமி`, `அம்மா`, `ஆசிரியர்`...).
3. **Character Voice Registry**:
   - When a character is registered, their assigned voice is locked for all subsequent dialogue appearances in the text.

---

## Architecture & Data Flow

```
+-------------------------------------------------------------+
|                      Browser Frontend                       |
|  - Dual Action Buttons: Expressive Audiobook vs Plain TTS   |
|  - Real-time Tagged Segment Breakdown & Voice Cast View    |
|  - Side-by-Side Comparative Audio Players                   |
+------------------------------+------------------------------+
                               | POST /generate (or /generate_baseline)
                               v
+-------------------------------------------------------------+
|                     Flask API (app.py)                      |
|  - Request Validation & Health Check Endpoints              |
|  - Native Cross-Origin Resource Sharing (CORS)              |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   NLP Tagger (tagger.py)                    |
|  - Dialogue & Narration Segmentation (Regex NLP)            |
|  - Gender Attribution & Persistent Character Tracking       |
|  - Navarasa Emotion Detection (Rate, Pitch, Volume)         |
+------------------------------+------------------------------+
                               | List[Segment]
                               v
+-------------------------------------------------------------+
|                 Audio Pipeline (pipeline.py)                |
|  - Async Edge-TTS Synthesis per Segment                     |
|  - PyDub Audio Stitching & Dynamic Pause Management         |
|  - 450ms Silence (Speaker Change) / 200ms (Same Speaker)   |
|  - MP3 Export to output/ directory                          |
+-------------------------------------------------------------+
```

---

## Quick Start

### Local Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/verycareful/KuralAI.git
   cd KuralAI
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required by PyDub for MP3 concatenation):
   - **Windows**: `winget install Gyan.FFmpeg` or download from ffmpeg.org
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt install ffmpeg`

4. **Launch Application**:
   ```bash
   python app.py
   ```
   Open **http://localhost:5000** in your browser.

5. **Run Automated Test Suite**:
   ```bash
   python tests.py
   ```

---

## Cloud Deployment

### 1. Render.com (1-Click Blueprint)

The repository includes a ready-to-deploy `render.yaml` configuration:
1. Connect repository on [Render Dashboard](https://dashboard.render.com).
2. Select **Blueprint** or **Web Service**.
3. Render builds the Docker container in the **Singapore** region with Python 3.12 and FFmpeg pre-configured.

### 2. Hugging Face Spaces (Docker)

1. Create a new Space on [Hugging Face Spaces](https://huggingface.co/new-space) with the **Docker** SDK.
2. Push repository:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/KuralAI
   git push space main
   ```

---

## Project Structure

```
.
|-- app.py              # Flask server with /generate, /generate_baseline, /voices, /examples
|-- tagger.py           # NLP engine: segmentation, gender mapping, emotion detection
|-- pipeline.py         # TTS synthesis (rate, pitch, volume) & audio stitching
|-- examples.py         # 8 curated Tamil example passages
|-- tests.py            # Comprehensive automated test suite
|-- Dockerfile          # Container specification with Python 3.12 & FFmpeg
|-- render.yaml         # Render deployment blueprint (Region: Singapore)
|-- requirements.txt    # Python dependencies (Flask, edge-tts, pydub)
|-- DIAGRAMS.md         # Architecture, sequence, state, and component diagrams
|-- static/
|   `-- index.html      # Single-page interface (vanilla HTML/CSS/JS)
`-- output/             # Generated audio files (gitignored)
```

---

## License

MIT License. Developed for open-source Tamil AI audio accessibility.
