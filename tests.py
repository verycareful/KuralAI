"""
tests.py — Automated test suite for Kural AI (Tagger, Emotion Detection, Examples).
"""

import sys
from tagger import tag_text, detect_emotion
from examples import EXAMPLES, get_all_titles, get_example_by_id


def test_tagger_segmentation():
    print("Testing tagger segmentation...")
    sample = 'அவன் வந்தான். "வணக்கம்!" என்றான் ராமன். "எப்படி இருக்கிறாய்?" என்று கேட்டாள் சீதா.'
    segs = tag_text(sample)

    assert len(segs) >= 3, f"Expected >=3 segments, got {len(segs)}"
    assert any(s.seg_type == "dialogue" for s in segs), "Dialogue not detected"
    assert any(s.seg_type == "narration" for s in segs), "Narration not detected"
    assert any(s.emotion == "excited" for s in segs), "Exclamation emotion not detected"
    assert any(s.emotion == "question" for s in segs), "Question emotion not detected"
    print("  ✅ Tagger segmentation tests passed")


def test_emotion_detection():
    print("Testing emotion detection...")
    cases = [
        # (input_text, expected_emotion)
        ("கோபம் வந்தது", "angry"),
        ("சினம் கொண்டு பார்த்தான்", "angry"),
        ("சோகம் நிறைந்தது", "sad"),
        ("கண்ணீர் வழிந்தது", "sad"),
        ("மகிழ்ச்சி பொங்கியது", "happy"),
        ("உற்சாகம் தந்தது", "happy"),
        ("பயம் வந்தது", "fear"),
        ("திகில் நிறைந்த இரவு", "fear"),
        ("ஆச்சரியம் ஆனது", "surprise"),
        ("வியப்புடன் பார்த்தான்", "surprise"),
        ("அன்பு நிறைந்தது", "tender"),
        ("அரவணைப்பு தந்தாள்", "tender"),
        ("என்ன நடந்தது?", "question"),
        ("வா போகலாம்!", "excited"),
        ("அவன் வீட்டிற்கு வந்தான்", "neutral"),
        # Substring false-positive regression test
        ("அவன் முகத்தில் சோகம் தெரிந்தது", "sad"),
    ]

    for text, expected in cases:
        actual = detect_emotion(text)
        assert actual == expected, f"Failed on '{text}': expected {expected}, got {actual}"

    print(f"  ✅ All {len(cases)} emotion keyword & punctuation tests passed")


def test_examples():
    print("Testing examples repository...")
    assert len(EXAMPLES) >= 8, f"Expected >=8 examples, got {len(EXAMPLES)}"
    titles = get_all_titles()
    assert len(titles) == len(EXAMPLES), "Title count mismatch"

    for ex in EXAMPLES:
        assert "id" in ex and "title" in ex and "text" in ex
        assert len(ex["text"]) > 50, f"Example '{ex['id']}' text too short"
        fetched = get_example_by_id(ex["id"])
        assert fetched is not None and fetched["id"] == ex["id"]

    print(f"  ✅ All {len(EXAMPLES)} example passages validated")


def main():
    print("=" * 60)
    print("  Kural AI — Running Test Suite")
    print("=" * 60)
    try:
        test_tagger_segmentation()
        test_emotion_detection()
        test_examples()
        print("=" * 60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
