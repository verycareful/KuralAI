"""
test_sample.py — Standalone test for the Tamil Audiobook Generator pipeline.

Runs the tagger on a sample Tamil paragraph, prints the tagged segments,
generates an MP3, and reports the output path.
"""

import sys
import time
from tagger import tag_text
from pipeline import generate

# ---------------------------------------------------------------------------
# Sample Tamil text with:
#   - Narration
#   - Multiple dialogue lines (2+ speakers)
#   - Exclamation (!)
#   - Question (?)
#   - Sad keyword (சோகம்)
#   - Happy keyword (மகிழ்ச்சி)
# ---------------------------------------------------------------------------
SAMPLE_TEXT = """
காலை வெயில் மெல்ல பரவியது. ராமன் தன் வீட்டின் முன் நின்று கொண்டிருந்தான்.
அவன் முகத்தில் சோகம் தெரிந்தது.

"என்ன ராமா, ஏன் இவ்வளவு சோகமாக இருக்கிறாய்?" என்றாள் சீதா.

"எனக்கு வேலை போய்விட்டது! என்ன செய்வது என்று தெரியவில்லை" என்றான் ராமன்.

சீதா அவனருகில் வந்தாள். அவள் கண்களில் கண்ணீர் தளும்பியது.

"கவலைப்படாதே! நாம் சேர்ந்து இதை சரி செய்வோம்" என்றாள் சீதா.

அப்போது முருகன் அங்கு வந்தான்.

"நண்பா, உனக்கு ஒரு நல்ல செய்தி இருக்கிறது! புதிய நிறுவனம் ஒன்று ஆட்களை தேடுகிறது" என்றான் முருகன்.

ராமன் முகத்தில் மகிழ்ச்சி பொங்கியது. "உண்மையா? அது மிகவும் நல்ல செய்தி!" என்றான் ராமன்.

மூவரும் சேர்ந்து சிரித்தார்கள். அந்த நாள் நம்பிக்கையுடன் முடிந்தது.
""".strip()


def main():
    print("=" * 70)
    print("  குரல் AI — Test Sample")
    print("=" * 70)

    # Step 1: Tag the text
    print("\n📝 Tagging text...\n")
    segments = tag_text(SAMPLE_TEXT)

    if not segments:
        print("❌ No segments produced!")
        sys.exit(1)

    # Display tagged segments
    print(f"  Found {len(segments)} segments:\n")
    print(f"  {'#':<3} {'Type':<12} {'Speaker':<14} {'Emotion':<10} {'Rate':<6} Text")
    print(f"  {'─'*3} {'─'*12} {'─'*14} {'─'*10} {'─'*6} {'─'*40}")

    for i, seg in enumerate(segments):
        d = seg.to_dict()
        text_preview = seg.text[:45] + ("..." if len(seg.text) > 45 else "")
        print(f"  {i:<3} {seg.seg_type:<12} {d['speaker_label']:<14} "
              f"{seg.emotion:<10} {seg.rate:<6} {text_preview}")

    # Step 2: Generate audio
    print(f"\n🎙️  Generating audio ({len(segments)} segments)...")
    start = time.time()

    try:
        output_filename, _ = generate(segments)
        elapsed = time.time() - start
        print(f"\n✅ Audio generated in {elapsed:.1f}s")
        print(f"   Output: output/{output_filename}")
        print(f"\n   Play it with: start output\\{output_filename}")
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
