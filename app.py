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


# ── Embedding model (pgvector RAG "personal model", plan §6.7) ────────────────
# EMBED_MODEL selects the sentence-transformers checkpoint exposed by /embed.
# Default: paraphrase-multilingual-MiniLM-L12-v2 (384-dim, multilingual incl.
# Bengali, CPU-friendly ~120 MB). Loaded fail-safe (mirrors the STT loader):
# if the checkpoint or sentence-transformers is unavailable, the service still
# starts and /embed returns 503 until the model can be loaded. The dependency
# itself is imported lazily so a missing package never crashes the service.
EMBED_MODEL = os.environ.get("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
embedder = None

try:
    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model (%s) ...", EMBED_MODEL)
    embedder = SentenceTransformer(EMBED_MODEL)
    logger.info(
        "Embedding model loaded (dim=%s)!",
        embedder.get_sentence_embedding_dimension(),
    )
except Exception as e:
    logger.error("Failed to load embedding model (%s): %s", EMBED_MODEL, e)
    logger.error("Service will start but /embed will return 503 until the model is available.")


@app.route("/health", methods=["GET"])
def health_check():
    stt_loaded = stt is not None
    embed_loaded = embedder is not None

    # STT is the primary capability; the embedder (pgvector RAG) is optional.
    # Report embedder readiness explicitly so callers can feature-detect /embed.
    body = {
        "status": "healthy" if stt_loaded and embed_loaded else "degraded",
        "stt": {"loaded": stt_loaded, "model": MODEL_SIZE},
        "embedder": {
            "loaded": embed_loaded,
            "model": EMBED_MODEL,
            "dimension": embedder.get_sentence_embedding_dimension() if embed_loaded else None,
        },
    }
    # STT down -> 503 (primary capability missing). Embedder-only missing is
    # still 200 (degraded) so /transcribe keeps working while /embed returns 503.
    code = 503 if not stt_loaded else 200
    return jsonify(body), code


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


@app.route("/embed", methods=["POST"])
def embed():
    """Embed one or more texts for the pgvector RAG "personal model" (plan §6.7).

    Request JSON:  {"texts": ["বিক্রি ৫০ টাকা", ...]}
    Response JSON: {"success": true, "dimension": 384,
                    "embeddings": [[...384...], ...]}
    """
    if embedder is None:
        return jsonify({"error": "Embedding model not loaded — service unavailable"}), 503

    data = request.get_json(silent=True)
    if not data or "texts" not in data:
        return jsonify({"error": "JSON body with 'texts' (a list of strings) is required"}), 400

    texts = data["texts"]
    if not isinstance(texts, list) or len(texts) == 0:
        return jsonify({"error": "'texts' must be a non-empty list of strings"}), 400
    if not all(isinstance(t, str) for t in texts):
        return jsonify({"error": "Every item in 'texts' must be a string"}), 400

    try:
        vectors = embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        embeddings = [list(map(float, vec)) for vec in vectors]
        return jsonify({
            "success": True,
            "dimension": len(embeddings[0]) if embeddings else 0,
            "embeddings": embeddings,
        })
    except Exception as e:
        logger.error("Embedding failed: %s", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
