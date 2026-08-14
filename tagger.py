"""
tagger.py — Regex-based speaker + emotion tagger for Tamil text.

Segments input text into dialogue and narration blocks,
assigns gender-consistent neural voices with persistent character tracking,
and detects emotion from punctuation and Tamil Navarasa keywords.
"""

import re
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict

# ---------------------------------------------------------------------------
# All 8 available Tamil Neural Voices across 4 regions
# ---------------------------------------------------------------------------
ALL_VOICES = [
    {"name": "ta-IN-PallaviNeural",  "label": "Pallavi",  "gender": "Female", "region": "India",     "accent": "Indian"},
    {"name": "ta-IN-ValluvarNeural", "label": "Valluvar", "gender": "Male",   "region": "India",     "accent": "Indian"},
    {"name": "ta-LK-KumarNeural",    "label": "Kumar",    "gender": "Male",   "region": "Sri Lanka", "accent": "Sri Lankan"},
    {"name": "ta-LK-SaranyaNeural",  "label": "Saranya",  "gender": "Female", "region": "Sri Lanka", "accent": "Sri Lankan"},
    {"name": "ta-MY-KaniNeural",     "label": "Kani",     "gender": "Female", "region": "Malaysia",  "accent": "Malaysian"},
    {"name": "ta-MY-SuryaNeural",    "label": "Surya",    "gender": "Male",   "region": "Malaysia",  "accent": "Malaysian"},
    {"name": "ta-SG-AnbuNeural",     "label": "Anbu",     "gender": "Male",   "region": "Singapore", "accent": "Singaporean"},
    {"name": "ta-SG-VenbaNeural",    "label": "Venba",    "gender": "Female", "region": "Singapore", "accent": "Singaporean"},
]

VOICES = ALL_VOICES
NARRATOR_ID = 0

MALE_VOICE_NAMES = [v["name"] for v in ALL_VOICES if v["gender"] == "Male"]
FEMALE_VOICE_NAMES = [v["name"] for v in ALL_VOICES if v["gender"] == "Female"]


def get_voice_map(narrator_voice: str = "ta-IN-PallaviNeural") -> dict:
    """
    Build default fallback mapping of speaker_id -> voice_name.
    speaker_id 0 = chosen narrator voice.
    speaker_id 1..7 = remaining available voices for dialogue characters.
    """
    valid_names = [v["name"] for v in ALL_VOICES]
    if narrator_voice not in valid_names:
        narrator_voice = "ta-IN-PallaviNeural"

    char_pool = [v["name"] for v in ALL_VOICES if v["name"] != narrator_voice]

    mapping = {0: narrator_voice}
    for i in range(1, 8):
        mapping[i] = char_pool[(i - 1) % len(char_pool)]

    return mapping


# ---------------------------------------------------------------------------
# Gender Lexicon & Morphological Grammar Markers
# ---------------------------------------------------------------------------
MALE_VERBS = [
    "என்றான்", "கேட்டான்", "சொன்னான்", "கூறினான்",
    "அலறினான்", "முணுமுணுத்தான்", "சிரித்தான்", "நின்றான்",
    "வந்தான்", "பார்த்தான்", "எழுந்தான்", "ஓடினான்", "கத்தினான்",
    "பதிலளித்தான்", "திடுக்கிட்டான்", "உணர்ந்தான்", "அறிவித்தார்"
]

FEMALE_VERBS = [
    "என்றாள்", "கேட்டாள்", "சொன்னாள்", "கூறினாள்",
    "அலறினாள்", "முணுமுணுத்தாள்", "சிரித்தாள்", "நின்றாள்",
    "வந்தாள்", "பார்த்தாள்", "எழுந்தாள்", "ஓடினாள்", "கத்தினாள்",
    "பதிலளித்தாள்", "திடுக்கிட்டாள்", "உணர்ந்தாள்"
]

MALE_NOUNS = [
    "அவன்", "அப்பா", "கணவன்", "மகன்", "அண்ணன்", "தம்பி", "தாத்தா",
    "தலைமை ஆசிரியர்", "ஆசிரியர்", "மருத்துவர்", "கடைக்காரன்", "மீனவன்",
    "சகோதரன்", "முதியவர்", "சிறுவன்", "முருகன்", "செல்வம்", "ராஜா",
    "கார்த்திக்", "வேலன்", "சுரேஷ்", "ரமேஷ்", "பிரவீன்", "முத்து", "ராமன்",
    "குமார்", "அருண்"
]

FEMALE_NOUNS = [
    "அவள்", "அம்மா", "மனைவி", "மகள்", "அக்கா", "தங்கை", "பாட்டி",
    "ஆசிரியை", "சகோதரி", "பெண்", "தாய்", "சிறுமி", "அனிதா",
    "தமிழ்ச்செல்வி", "மீனாட்சி", "வசந்தா", "சரோஜா", "கமலா", "பிரியா",
    "லட்சுமி", "வள்ளி", "சீதா", "கவிதா", "ராதா", "சங்கீதா"
]


# ---------------------------------------------------------------------------
# Emotion keyword lists (stems / partial matches)
# Expanded from Navarasa tradition + modern Tamil emotional vocabulary
# ---------------------------------------------------------------------------

SAD_KEYWORDS = [
    "அழு", "அழுகை", "கண்ணீர்", "வருத்தம்", "சோகம்", "துக்கம்",
    "வலி", "பரிதாபம்", "துன்பம்", "வேதனை", "கஷ்டம்",
    "இழப்பு", "பிரிவு", "தனிமை", "ஏக்கம்", "புலம்பல்",
    "கவலை", "கலக்கம்", "மனவேதனை", "நொந்து", "உடைந்து",
    "கருணை", "இரக்கம்", "பரிவு",
]

ANGRY_KEYWORDS = [
    "கோபம்", "சினம்", "ஆத்திரம்", "கோபமா",
    "கத்த", "கொதிப்", "ரோஷம்", "வெகுளி", "சீற்றம்",
    "வெறுப்பு", "ஆவேசம்", "வெகுண்டு", "கடுப்பு",
    "ரௌத்திரம்", "உக்கிரம்",
]

HAPPY_KEYWORDS = [
    "மகிழ்ச்சி", "சந்தோஷம்", "மகிழ்", "ஆனந்தம்",
    "சிரி", "சிரிப்பு", "களிப்", "களிப்பு", "நகை",
    "உற்சாகம்", "உவகை", "கொண்டாட", "பெருமிதம்", "பெருமை",
    "நிம்மதி", "திருப்தி", "மனநிறைவு",
]

FEAR_KEYWORDS = [
    "பயம்", "அச்சம்", "பயந்து", "பயமா",
    "திகில்", "நடுக்கம்", "நடுங்கி", "பீதி", "அதிர்ச்சி",
    "பதற்றம்", "பரபரப்பு", "கலக்கம்", "திடுக்கிட்டு",
    "பயானகம்", "அஞ்சி",
]

SURPRISE_KEYWORDS = [
    "ஆச்சரியம்", "வியப்பு", "அதிசயம்",
    "அற்புதம்", "அதிர்ச்சி", "திகைப்பு", "திகைத்து",
    "நம்பமுடியவில்லை", "நம்பவேமுடியல", "ஆச்சரியப்பட்டு",
    "அட", "அடடா", "ஆஹா", "ஐயோ",
]

TENDER_KEYWORDS = [
    "அன்பு", "காதல்", "பாசம்", "நேசம்",
    "அரவணைப்பு", "பரிவு", "அக்கறை", "ஆறுதல்",
    "ஏக்கம்", "தாகம்", "பக்தி",
]

# ---------------------------------------------------------------------------
# SSML Prosody Modulation Rules (Rate, Pitch, Volume)
# ---------------------------------------------------------------------------
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

EMOTION_PITCH = {
    "neutral":   "+0Hz",
    "excited":   "+6Hz",
    "question":  "+5Hz",
    "sad":       "-6Hz",
    "angry":     "+6Hz",
    "happy":     "+4Hz",
    "fear":      "+8Hz",
    "surprise":  "+10Hz",
    "tender":    "-3Hz",
}

EMOTION_VOLUME = {
    "neutral":   "+0%",
    "excited":   "+10%",
    "question":  "+0%",
    "sad":       "-10%",
    "angry":     "+15%",
    "happy":     "+5%",
    "fear":      "+5%",
    "surprise":  "+10%",
    "tender":    "-15%",
}


# ---------------------------------------------------------------------------
# Segment data class
# ---------------------------------------------------------------------------
@dataclass
class Segment:
    text: str
    seg_type: str        # "dialogue" or "narration"
    speaker_id: int      # speaker identifier
    emotion: str         # "neutral", "excited", "question", "sad", "angry", "happy", "fear", "surprise", "tender"
    rate: str            # edge-tts rate string e.g. "+15%"
    pitch: str = "+0Hz"  # edge-tts pitch string e.g. "+6Hz"
    volume: str = "+0%" # edge-tts volume string e.g. "+15%"
    speaker_name: str = "" # detected character name e.g. "முருகன்", "லட்சுமி"
    gender: str = "Neutral" # "Male", "Female", "Neutral"
    voice: str = "ta-IN-PallaviNeural"

    def to_dict(self):
        d = asdict(self)
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
    if "!" in text or "\uff01" in text:
        return "excited"
    if "?" in text or "\uff1f" in text:
        return "question"

    return "neutral"


# ---------------------------------------------------------------------------
# Quote splitting — handles Tamil/smart quotes and ASCII quotes
# ---------------------------------------------------------------------------
QUOTE_PATTERN = re.compile(
    r'[\u201C\u201D""\u00AB\u00BB]'   # opening quote chars
    r'(.+?)'                           # captured dialogue text
    r'[\u201C\u201D""\u00AB\u00BB]'   # closing quote chars
    r'|'
    r'"(.+?)"'                         # ASCII double quotes
)


def _split_into_raw_segments(text: str) -> List[dict]:
    """
    Split text into alternating narration and dialogue segments with contextual windows.
    Returns list of {"text": ..., "is_dialogue": bool, "context_before": str, "context_after": str}
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
                    "context_before": "",
                    "context_after": "",
                })

        # The dialogue itself
        dialogue_text = match.group(1) or match.group(2)
        if dialogue_text and dialogue_text.strip():
            context_before = text[max(0, start - 80):start]
            context_after = text[end:min(len(text), end + 80)]
            segments.append({
                "text": dialogue_text.strip(),
                "is_dialogue": True,
                "context_before": context_before,
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
                "context_before": "",
                "context_after": "",
            })

    if not segments:
        segments.append({
            "text": text.strip(),
            "is_dialogue": False,
            "context_before": "",
            "context_after": "",
        })

    return segments


# ---------------------------------------------------------------------------
# Speaker & Gender Attribution
# ---------------------------------------------------------------------------
def _detect_speaker_and_gender(context_before: str, context_after: str) -> Tuple[str, str]:
    """
    Detect character name and gender from surrounding context.
    Returns (character_name, gender) where gender is 'Male', 'Female', or 'Unknown'.
    """
    # 1. Check for female verbs in context_after first (e.g. "..." என்றாள் அனிதா)
    for verb in FEMALE_VERBS:
        if verb in context_after:
            # Extract name following verb
            after_part = context_after[context_after.find(verb) + len(verb):].strip()
            tokens = re.split(r'[.,;:!?\s]+', after_part)
            name = tokens[0] if tokens and tokens[0] else ""
            if not name or len(name) < 2:
                # Check for female noun in surrounding context
                for n in FEMALE_NOUNS:
                    if n in context_before or n in context_after:
                        name = n
                        break
            return (name or "Female Character", "Female")

    # 2. Check for male verbs in context_after (e.g. "..." என்றான் முருகன்)
    for verb in MALE_VERBS:
        if verb in context_after:
            after_part = context_after[context_after.find(verb) + len(verb):].strip()
            tokens = re.split(r'[.,;:!?\s]+', after_part)
            name = tokens[0] if tokens and tokens[0] else ""
            if not name or len(name) < 2:
                for n in MALE_NOUNS:
                    if n in context_before or n in context_after:
                        name = n
                        break
            return (name or "Male Character", "Male")

    # 3. Check for female verbs/nouns in context_before (e.g. அனிதா பார்த்தாள். "...")
    for verb in FEMALE_VERBS:
        if verb in context_before:
            for n in FEMALE_NOUNS:
                if n in context_before:
                    return (n, "Female")
            return ("Female Character", "Female")

    for verb in MALE_VERBS:
        if verb in context_before:
            for n in MALE_NOUNS:
                if n in context_before:
                    return (n, "Male")
            return ("Male Character", "Male")

    # 4. Check standalone character nouns in context
    for n in FEMALE_NOUNS:
        if n in context_before or n in context_after:
            return (n, "Female")

    for n in MALE_NOUNS:
        if n in context_before or n in context_after:
            return (n, "Male")

    return ("", "Unknown")


def _assign_speakers(raw_segments: List[dict], narrator_voice: str = "ta-IN-PallaviNeural") -> Tuple[List[dict], Dict[int, str]]:
    """
    Assign persistent speaker IDs and gender-appropriate neural voices.
    - Characters with the same name always receive the EXACT SAME voice and speaker ID.
    - Male characters receive Male neural voices.
    - Female characters receive Female neural voices.
    """
    # Separate available male and female voices (excluding narrator voice)
    male_pool = [v["name"] for v in ALL_VOICES if v["gender"] == "Male" and v["name"] != narrator_voice]
    female_pool = [v["name"] for v in ALL_VOICES if v["gender"] == "Female" and v["name"] != narrator_voice]

    if not male_pool:
        male_pool = [v["name"] for v in ALL_VOICES if v["gender"] == "Male"]
    if not female_pool:
        female_pool = [v["name"] for v in ALL_VOICES if v["gender"] == "Female"]

    character_registry: Dict[str, dict] = {}
    next_speaker_id = 1
    next_male_idx = 0
    next_female_idx = 0

    voice_map: Dict[int, str] = {0: narrator_voice}

    for seg in raw_segments:
        if not seg["is_dialogue"]:
            seg["speaker_id"] = 0
            seg["speaker_name"] = "Narrator"
            seg["gender"] = "Neutral"
            seg["voice"] = narrator_voice
        else:
            ctx_before = seg.get("context_before", "")
            ctx_after = seg.get("context_after", "")

            char_name, gender = _detect_speaker_and_gender(ctx_before, ctx_after)

            # Check if this character has already been assigned a voice in this story
            if char_name and char_name in character_registry:
                reg = character_registry[char_name]
                seg["speaker_id"] = reg["speaker_id"]
                seg["speaker_name"] = char_name
                seg["gender"] = reg["gender"]
                seg["voice"] = reg["voice"]
            else:
                # Assign a voice strictly matching the character's gender
                if gender == "Female":
                    assigned_voice = female_pool[next_female_idx % len(female_pool)]
                    next_female_idx += 1
                elif gender == "Male":
                    assigned_voice = male_pool[next_male_idx % len(male_pool)]
                    next_male_idx += 1
                else:
                    # Alternate if gender is unspecified
                    if next_female_idx <= next_male_idx:
                        assigned_voice = female_pool[next_female_idx % len(female_pool)]
                        gender = "Female"
                        next_female_idx += 1
                    else:
                        assigned_voice = male_pool[next_male_idx % len(male_pool)]
                        gender = "Male"
                        next_male_idx += 1

                sid = next_speaker_id
                next_speaker_id += 1
                voice_map[sid] = assigned_voice

                if char_name:
                    character_registry[char_name] = {
                        "speaker_id": sid,
                        "gender": gender,
                        "voice": assigned_voice
                    }

                seg["speaker_id"] = sid
                seg["speaker_name"] = char_name or f"Character {sid}"
                seg["gender"] = gender
                seg["voice"] = assigned_voice

    return raw_segments, voice_map


# ---------------------------------------------------------------------------
# Main tagging function
# ---------------------------------------------------------------------------
def tag_text(text: str, narrator_voice: str = "ta-IN-PallaviNeural") -> List[Segment]:
    """
    Main entry point. Takes raw Tamil text, returns a list of Segment objects
    with gender-consistent speaker assignment and Navarasa prosody modulation.
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Step 1: split into dialogue / narration
    raw_segments = _split_into_raw_segments(text)

    # Step 2: assign speakers and gender-consistent voices
    raw_segments, voice_map = _assign_speakers(raw_segments, narrator_voice=narrator_voice)

    # Step 3: detect emotion and build Segment objects
    result = []
    for seg in raw_segments:
        emotion = detect_emotion(seg["text"])
        rate = EMOTION_RATE.get(emotion, "+0%")
        pitch = EMOTION_PITCH.get(emotion, "+0Hz")
        volume = EMOTION_VOLUME.get(emotion, "+0%")

        segment = Segment(
            text=seg["text"],
            seg_type="dialogue" if seg["is_dialogue"] else "narration",
            speaker_id=seg["speaker_id"],
            emotion=emotion,
            rate=rate,
            pitch=pitch,
            volume=volume,
            speaker_name=seg.get("speaker_name", ""),
            gender=seg.get("gender", "Neutral"),
            voice=seg.get("voice", narrator_voice),
        )
        result.append(segment)

    return result


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
        print(f"[{i}] {seg.seg_type:10s} | speaker={seg.speaker_id} ({seg.gender}: {seg.voice}) | "
              f"emotion={seg.emotion:10s} | rate={seg.rate:5s} | pitch={seg.pitch:5s} | {seg.text[:50]}...")
