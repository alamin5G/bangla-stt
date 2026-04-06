from flask import Flask, request, jsonify
from flask_cors import CORS
from banglaspeech2text import Speech2Text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Model load হবে startup-এ (একবার, প্রতিটা request-এ না)
logger.info("Loading BanglaSpeech2Text model...")
stt = Speech2Text("small")   # "small" = 1GB, balance of accuracy & speed
logger.info("Model loaded successfully!")

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})

@app.route("/transcribe", methods=["POST"])
def transcribe():
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
        logger.error(f"Transcription failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/transcribe/segments", methods=["POST"])
def transcribe_segments():
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
