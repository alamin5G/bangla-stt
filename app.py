import os
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
from banglaspeech2text import Speech2Text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Allow audio files up to 16 MB (default Flask limit is 16 KB — too small for voice recordings)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

# ── Model loading with graceful failure ──────────────────────────────────────
# MODEL_SIZE env var controls which banglaspeech2text model to load:
#   "small"  → ~1 GB RAM, faster, less accurate (good for dev)
#   "large"  → ~3-4 GB RAM, slower, more accurate (good for production)
# If loading fails, the service starts but /transcribe returns 503.
MODEL_SIZE = os.environ.get("MODEL_SIZE", "small")
stt = None

try:
    logger.info("Loading BanglaSpeech2Text model (size=%s) ...", MODEL_SIZE)
    stt = Speech2Text(MODEL_SIZE)
    logger.info("Model loaded successfully (size=%s)!", MODEL_SIZE)
except Exception as e:
    logger.error("Failed to load STT model (size=%s): %s", MODEL_SIZE, e)
    logger.error("Service will start but /transcribe will return 503 until model is available.")


@app.route("/health", methods=["GET"])
def health_check():
    if stt is None:
        return jsonify({"status": "degraded", "error": "STT model not loaded"}), 503
    return jsonify({"status": "healthy", "model": MODEL_SIZE})


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if stt is None:
        return jsonify({"error": "STT model not loaded — service unavailable"}), 503

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    try:
        audio_bytes = audio_file.read()
        transcription = stt.recognize(audio_bytes)
        return jsonify({
            "success": True,
            "text": transcription
        })
    except Exception as e:
        logger.error("Transcription failed: %s", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/transcribe/segments", methods=["POST"])
def transcribe_segments():
    if stt is None:
        return jsonify({"error": "STT model not loaded — service unavailable"}), 503

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    try:
        audio_bytes = audio_file.read()
        segments = stt.recognize(audio_bytes, return_segments=True)
        result = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        return jsonify({"success": True, "segments": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
