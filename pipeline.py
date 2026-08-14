"""
pipeline.py — Audio generation pipeline.

Takes tagged segments from tagger.py, synthesizes each with edge-tts,
and stitches them into a single MP3 with appropriate pauses.
"""

import asyncio
import os
import uuid
import tempfile
import shutil
from typing import List, Tuple

import edge_tts
from pydub import AudioSegment

from tagger import Segment, ALL_VOICES, get_voice_map

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SPEAKER_CHANGE_PAUSE_MS = 450   # pause between different speakers
SAME_SPEAKER_PAUSE_MS   = 200   # pause between same-speaker segments
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Single-segment TTS
# ---------------------------------------------------------------------------
async def _synthesize_segment(segment: Segment, output_path: str, voice_map: dict = None) -> str:
    """Synthesize a single segment to an MP3 file using edge-tts."""
    if voice_map and segment.speaker_id in voice_map:
        voice_name = voice_map[segment.speaker_id]
    else:
        voice_name = "ta-IN-PallaviNeural"

    communicate = edge_tts.Communicate(
        text=segment.text,
        voice=voice_name,
        rate=segment.rate,
    )
    await communicate.save(output_path)
    return output_path


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
async def _generate_async(segments: List[Segment], narrator_voice: str = "ta-IN-PallaviNeural") -> Tuple[str, List[dict]]:
    """
    Async core of the pipeline.
    1. Synthesize each segment to a temp MP3 using the chosen voice mapping
    2. Stitch them with pydub, inserting pauses on speaker changes
    3. Export the final MP3
    Returns (output_path, segment_dicts)
    """
    ensure_output_dir()

    if not segments:
        raise ValueError("No segments to synthesize")

    tmp_dir = tempfile.mkdtemp(prefix="kural_ai_")
    voice_map = get_voice_map(narrator_voice)

    try:
        # Step 1: Synthesize all segments
        temp_files = []
        for i, seg in enumerate(segments):
            tmp_path = os.path.join(tmp_dir, f"seg_{i:04d}.mp3")
            await _synthesize_segment(seg, tmp_path, voice_map=voice_map)
            temp_files.append(tmp_path)

        # Step 2: Load and stitch with pydub
        silence_speaker_change = AudioSegment.silent(duration=SPEAKER_CHANGE_PAUSE_MS)
        silence_same_speaker   = AudioSegment.silent(duration=SAME_SPEAKER_PAUSE_MS)

        combined = AudioSegment.empty()
        prev_speaker_id = None

        for i, (seg, tmp_path) in enumerate(zip(segments, temp_files)):
            audio_seg = AudioSegment.from_mp3(tmp_path)

            if i > 0:
                if seg.speaker_id != prev_speaker_id:
                    combined += silence_speaker_change
                else:
                    combined += silence_same_speaker

            combined += audio_seg
            prev_speaker_id = seg.speaker_id

        # Step 3: Export final MP3
        job_id = uuid.uuid4().hex[:12]
        output_filename = f"{job_id}.mp3"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        combined.export(output_path, format="mp3")

        # Build segment dicts for API response, adding active voice name
        segment_dicts = []
        for seg in segments:
            d = seg.to_dict()
            d["voice"] = voice_map.get(seg.speaker_id, "ta-IN-PallaviNeural")
            segment_dicts.append(d)

        return output_filename, segment_dicts

    finally:
        # Clean up temp files
        shutil.rmtree(tmp_dir, ignore_errors=True)


def generate(segments: List[Segment], narrator_voice: str = "ta-IN-PallaviNeural") -> Tuple[str, List[dict]]:
    """
    Synchronous wrapper for the async pipeline.
    Returns (output_filename, segment_dicts).
    """
    return asyncio.run(_generate_async(segments, narrator_voice=narrator_voice))


# ---------------------------------------------------------------------------
# CLI quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from tagger import tag_text

    sample = (
        'அந்த மாலை நேரத்தில் ராமன் வீட்டிற்கு வந்தான். '
        '"நான் மிகவும் சோகமாக இருக்கிறேன்!" என்றான் ராமன். '
        'சீதா அவனைப் பார்த்தாள். '
        '"என்ன நடந்தது?" என்றாள் சீதா.'
    )

    print("Tagging text...")
    segments = tag_text(sample)
    for seg in segments:
        print(f"  [{seg.speaker_id}] {seg.seg_type:10s} {seg.emotion:10s} → {seg.text[:50]}...")

    print("\nGenerating audio...")
    filename, seg_dicts = generate(segments)
    print(f"✓ Output: output/{filename}")
