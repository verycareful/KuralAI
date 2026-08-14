"""
tagger.py — Regex-based speaker + emotion tagger for Tamil text.

Segments input text into dialogue and narration blocks,
assigns speakers via round-robin with attribution heuristics,
and detects emotion from punctuation and Tamil keywords.
"""

import re
from dataclasses import dataclass, asdict
from typing import List

# ---------------------------------------------------------------------------
# Voice cast
# ---------------------------------------------------------------------------
VOICES = [
    {"id": 0, "name": "ta-IN-PallaviNeural",  "label": "Narrator",    "gender": "F", "accent": "Indian"},
    {"id": 1, "name": "ta-IN-ValluvarNeural",  "label": "Character 1", "gender": "M", "accent": "Indian"},
    {"id": 2, "name": "ta-LK-KumarNeural",     "label": "Character 2", "gender": "M", "accent": "Sri Lankan"},
    {"id": 3, "name": "ta-LK-SaranyaNeural",   "label": "Character 3", "gender": "F", "accent": "Sri Lankan"},
]

NARRATOR_ID = 0
DIALOGUE_VOICE_IDS = [1, 2, 3]  # round-robin pool for dialogue speakers

# ---------------------------------------------------------------------------
# Emotion keyword lists (stems / partial matches)
# Expanded from Navarasa tradition + modern Tamil emotional vocabulary
# ---------------------------------------------------------------------------

SAD_KEYWORDS = [
    # Core sadness
    "அழு", "அழுகை", "கண்ணீர்", "வருத்தம்", "சோகம்", "துக்கம்",
    # Pain & suffering
    "வலி", "பரிதாபம்", "துன்பம்", "வேதனை", "கஷ்டம்",
    # Grief & mourning
    "இழப்பு", "பிரிவு", "தனிமை", "ஏக்கம்", "புலம்பல்",
    # Worry & distress
    "கவலை", "கலக்கம்", "மனவேதனை", "நொந்து", "உடைந்து",
    # Literary / formal
    "கருணை", "இரக்கம்", "பரிவு",
]

ANGRY_KEYWORDS = [
    # Core anger
    "கோபம்", "சினம்", "ஆத்திரம்", "கோபமா",
    # Shouting & fury
    "கத்த", "கொதிப்", "ரோஷம்", "வெகுளி", "சீற்றம்",
    # Rage & aggression
    "வெறுப்பு", "ஆவேசம்", "வெகுண்டு", "கடுப்பு",
    # Literary / formal
    "ரௌத்திரம்", "உக்கிரம்",
]

HAPPY_KEYWORDS = [
    # Core happiness
    "மகிழ்ச்சி", "சந்தோஷம்", "மகிழ்", "ஆனந்தம்",
    # Joy & laughter
    "சிரி", "சிரிப்பு", "களிப்", "களிப்பு", "நகை",
    # Enthusiasm & celebration
    "உற்சாகம்", "உவகை", "கொண்டாட", "பெருமிதம்", "பெருமை",
    # Relief & contentment
    "நிம்மதி", "திருப்தி", "மனநிறைவு",
]

FEAR_KEYWORDS = [
    # Core fear
    "பயம்", "அச்சம்", "பயந்து", "பயமா",
    # Terror & dread
    "திகில்", "நடுக்கம்", "நடுங்கி", "பீதி", "அதிர்ச்சி",
    # Anxiety & unease
    "பதற்றம்", "பரபரப்பு", "கலக்கம்", "திடுக்கிட்டு",
    # Literary
    "பயானகம்", "அஞ்சி",
]

SURPRISE_KEYWORDS = [
    # Core surprise
    "ஆச்சரியம்", "வியப்பு", "அதிசயம்",
    # Amazement & wonder
    "அற்புதம்", "அதிர்ச்சி", "திகைப்பு", "திகைத்து",
    # Disbelief
    "நம்பமுடியவில்லை", "நம்பவேமுடியல", "ஆச்சரியப்பட்டு",
    # Exclamation
    "அட", "அடடா", "ஆஹா", "ஐயோ",
]

TENDER_KEYWORDS = [
    # Love & affection
    "அன்பு", "காதல்", "பாசம்", "நேசம்",
    # Warmth & care
    "அரவணைப்பு", "பரிவு", "அக்கறை", "ஆறுதல்",
    # Longing & devotion
    "ஏக்கம்", "தாகம்", "பக்தி",
]

# Emotion → edge-tts rate string + pitch hint
EMOTION_RATE = {
    "neutral":   "+0%",
    "excited":   "+10%",
    "question":  "+5%",
    "sad":       "-15%",
    "angry":     "+15%",
    "happy":     "+5%",
    "fear":      "+8%",
    "surprise":  "+12%",
    "tender":    "-8%",
}


# ---------------------------------------------------------------------------
# Attribution verbs — used to detect who is speaking near a quote
# ---------------------------------------------------------------------------
ATTRIBUTION_VERBS = [
    "என்றார்", "என்றாள்", "என்றான்", "என்று",
    "கேட்டார்", "கேட்டாள்", "கேட்டான்",
    "சொன்னார்", "சொன்னாள்", "சொன்னான்",
    "கூறினார்", "கூறினாள்", "கூறினான்",
    "பதிலளித்தார்", "பதிலளித்தாள்", "பதிலளித்தான்",
]

# Build a regex that matches: <attribution_verb> <optional_name>
_attr_pattern = r'(?:' + '|'.join(re.escape(v) for v in ATTRIBUTION_VERBS) + r')\s*(\S+)?'
ATTRIBUTION_RE = re.compile(_attr_pattern)

# ---------------------------------------------------------------------------
# Segment data class
# ---------------------------------------------------------------------------
@dataclass
class Segment:
    text: str
    seg_type: str        # "dialogue" or "narration"
    speaker_id: int      # index into VOICES
    emotion: str         # "neutral", "excited", "question", "sad", "angry", "happy"
    rate: str            # edge-tts rate string

    def to_dict(self):
        d = asdict(self)
        d["voice"] = VOICES[self.speaker_id]["name"]
        d["speaker_label"] = VOICES[self.speaker_id]["label"]
        return d


# ---------------------------------------------------------------------------
# Emotion detection
# ---------------------------------------------------------------------------
def _keyword_in_text(keyword: str, text: str) -> bool:
    """Check if a Tamil keyword appears as a standalone word (not inside another Tamil word)."""
    start = 0
    while True:
        idx = text.find(keyword, start)
        if idx == -1:
            return False
        # Check character before the match — should not be a Tamil letter
        if idx > 0:
            prev_char = ord(text[idx - 1])
            if 0x0B80 <= prev_char <= 0x0BFF:
                start = idx + 1
                continue
        return True


def detect_emotion(text: str) -> str:
    """Detect emotion from punctuation and Tamil keywords."""
    # Keyword-based detection takes priority (more specific)
    # Order: high-arousal emotions first, then low-arousal
    for kw in ANGRY_KEYWORDS:
        if _keyword_in_text(kw, text):
            return "angry"
    for kw in FEAR_KEYWORDS:
        if _keyword_in_text(kw, text):
            return "fear"
    for kw in SAD_KEYWORDS:
        if _keyword_in_text(kw, text):
            return "sad"
    for kw in SURPRISE_KEYWORDS:
        if _keyword_in_text(kw, text):
            return "surprise"
    for kw in HAPPY_KEYWORDS:
        if _keyword_in_text(kw, text):
            return "happy"
    for kw in TENDER_KEYWORDS:
        if _keyword_in_text(kw, text):
            return "tender"

    # Punctuation-based fallback
    if "!" in text or "\uff01" in text:  # ASCII and fullwidth exclamation
        return "excited"
    if "?" in text or "\uff1f" in text:  # ASCII and fullwidth question
        return "question"

    return "neutral"


# ---------------------------------------------------------------------------
# Quote splitting — handles Tamil/smart quotes and ASCII quotes
# ---------------------------------------------------------------------------
# Pattern matches quoted text with various quote styles
QUOTE_PATTERN = re.compile(
    r'[\u201C\u201D""\u00AB\u00BB]'   # opening quote chars
    r'(.+?)'                           # captured dialogue text
    r'[\u201C\u201D""\u00AB\u00BB]'   # closing quote chars
    r'|'
    r'"(.+?)"'                         # ASCII double quotes
)


def _split_into_raw_segments(text: str) -> List[dict]:
    """
    Split text into alternating narration and dialogue segments.
    Returns list of {"text": ..., "is_dialogue": bool, "context_after": str}
    """
    segments = []
    last_end = 0

    for match in QUOTE_PATTERN.finditer(text):
        start, end = match.span()

        # Narration before this quote
        if start > last_end:
            narr_text = text[last_end:start].strip()
            if narr_text:
                segments.append({
                    "text": narr_text,
                    "is_dialogue": False,
                    "context_after": "",
                })

        # The dialogue itself
        dialogue_text = match.group(1) or match.group(2)
        if dialogue_text and dialogue_text.strip():
            # Grab a bit of text after the quote for attribution detection
            context_after = text[end:end + 80] if end < len(text) else ""
            segments.append({
                "text": dialogue_text.strip(),
                "is_dialogue": True,
                "context_after": context_after,
            })

        last_end = end

    # Trailing narration
    if last_end < len(text):
        trailing = text[last_end:].strip()
        if trailing:
            segments.append({
                "text": trailing,
                "is_dialogue": False,
                "context_after": "",
            })

    # If no quotes found at all, treat entire text as narration
    if not segments:
        segments.append({
            "text": text.strip(),
            "is_dialogue": False,
            "context_after": "",
        })

    return segments


# ---------------------------------------------------------------------------
# Speaker assignment
# ---------------------------------------------------------------------------
def _assign_speakers(raw_segments: List[dict]) -> List[dict]:
    """
    Assign speaker IDs:
    - Narration always gets NARRATOR_ID (0)
    - Dialogue gets round-robin from DIALOGUE_VOICE_IDS
    - If attribution text is detected after a quote, try to keep
      the same name → same speaker mapping for consistency
    """
    name_to_speaker = {}
    dialogue_counter = 0

    for seg in raw_segments:
        if not seg["is_dialogue"]:
            seg["speaker_id"] = NARRATOR_ID
        else:
            # Try attribution detection
            assigned = False
            context = seg.get("context_after", "")
            attr_match = ATTRIBUTION_RE.search(context)
            if attr_match and attr_match.group(1):
                name = attr_match.group(1).strip(".,;:!? ")
                if name and len(name) > 1:
                    if name in name_to_speaker:
                        seg["speaker_id"] = name_to_speaker[name]
                        assigned = True
                    else:
                        # Assign next available dialogue voice
                        sid = DIALOGUE_VOICE_IDS[dialogue_counter % len(DIALOGUE_VOICE_IDS)]
                        name_to_speaker[name] = sid
                        dialogue_counter += 1
                        seg["speaker_id"] = sid
                        assigned = True

            if not assigned:
                # Simple round-robin
                seg["speaker_id"] = DIALOGUE_VOICE_IDS[dialogue_counter % len(DIALOGUE_VOICE_IDS)]
                dialogue_counter += 1

    return raw_segments


# ---------------------------------------------------------------------------
# Main tagging function
# ---------------------------------------------------------------------------
def tag_text(text: str) -> List[Segment]:
    """
    Main entry point. Takes raw Tamil text, returns a list of Segment objects
    with speaker assignment and emotion detection.
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Step 1: split into dialogue / narration
    raw_segments = _split_into_raw_segments(text)

    # Step 2: assign speakers
    raw_segments = _assign_speakers(raw_segments)

    # Step 3: detect emotion and build Segment objects
    result = []
    for seg in raw_segments:
        emotion = detect_emotion(seg["text"])
        rate = EMOTION_RATE.get(emotion, "+0%")
        segment = Segment(
            text=seg["text"],
            seg_type="dialogue" if seg["is_dialogue"] else "narration",
            speaker_id=seg["speaker_id"],
            emotion=emotion,
            rate=rate,
        )
        result.append(segment)

    return result


# ---------------------------------------------------------------------------
# CLI quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = (
        'அந்த மாலை நேரத்தில் ராமன் வீட்டிற்கு வந்தான். '
        '"நான் மிகவும் சோகமாக இருக்கிறேன்!" என்றான் ராமன். '
        'சீதா அவனைப் பார்த்தாள். '
        '"என்ன நடந்தது?" என்றாள் சீதா. '
        '"எனக்கு வேலை போய்விட்டது!" என்றான் ராமன். '
        'சீதா அவனை ஆறுதல் செய்தாள். '
        '"கவலைப்படாதே, எல்லாம் சரியாகும்" என்றாள் சீதா.'
    )
    segments = tag_text(sample)
    for i, seg in enumerate(segments):
        print(f"[{i}] {seg.seg_type:10s} | speaker={seg.speaker_id} | "
              f"emotion={seg.emotion:10s} | rate={seg.rate:5s} | {seg.text[:60]}...")
