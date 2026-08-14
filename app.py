"""
app.py — Flask backend for the Expressive Tamil Audiobook Generator.

Endpoints:
  GET  /              → serves the frontend
  POST /generate      → accepts {"text": "..."}, returns {"audio_url": ..., "segments": [...]}
  GET  /voices        → returns the voice cast
  GET  /examples      → returns list of curated example passages
  GET  /examples/<id> → returns a specific example's full text
  GET  /output/<f>    → serves generated MP3 files
"""

import os
import traceback

from flask import Flask, request, jsonify, send_from_directory, send_file

from tagger import tag_text, VOICES
from pipeline import generate, OUTPUT_DIR, ensure_output_dir
from examples import EXAMPLES, get_example_by_id, get_all_titles

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
)

# Ensure output directory exists at startup
ensure_output_dir()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the single-page frontend."""
    return send_file(os.path.join(app.static_folder, "index.html"))


@app.route("/generate", methods=["POST"])
def generate_audio():
    """
    Accept Tamil text, run tagger + pipeline, return audio URL and segments.

    Request body: {"text": "Tamil text here..."}
    Response:     {"audio_url": "/output/abc123.mp3", "segments": [...]}
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field in request body"}), 400

        text = data["text"].strip()
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400

        if len(text) > 10000:
            return jsonify({"error": "Text too long. Please keep it under 10,000 characters for the demo."}), 400

        # Step 1: Tag the text
        segments = tag_text(text)
        if not segments:
            return jsonify({"error": "Could not parse any segments from the text"}), 400

        # Step 2: Generate audio
        output_filename, segment_dicts = generate(segments)

        return jsonify({
            "audio_url": f"/output/{output_filename}",
            "segments": segment_dicts,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500


@app.route("/voices", methods=["GET"])
def get_voices():
    """Return the voice cast for display in the frontend."""
    return jsonify({"voices": VOICES})


@app.route("/examples", methods=["GET"])
def list_examples():
    """Return the list of curated Tamil example passages."""
    return jsonify({"examples": get_all_titles()})


@app.route("/examples/<example_id>", methods=["GET"])
def get_example(example_id):
    """Return a specific example's full text."""
    ex = get_example_by_id(example_id)
    if not ex:
        return jsonify({"error": f"Example '{example_id}' not found"}), 404
    return jsonify(ex)


@app.route("/output/<path:filename>")
def serve_output(filename):
    """Serve generated MP3 files."""
    return send_from_directory(OUTPUT_DIR, filename, mimetype="audio/mpeg")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  குரல் AI — Expressive Tamil Audiobook Generator")
    print("  http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
