# 🎤 Bangla Speech-to-Text Docker Service

A production-ready **Dockerized REST API** for converting Bengali (Bangla) speech to text using the [BanglaSpeech2Text](https://github.com/shhossain/BanglaSpeech2Text) library. Built on OpenAI's Whisper model with CTranslate2 for fast inference.

```
🎤 Voice Input → Docker Container (BanglaSpeech2Text) → 📝 Bangla Text Output
```

---

## ✨ Features

- **Offline Processing** — Once the model is downloaded, no internet required
- **No API Key Needed** — 100% free, uses open-source Whisper models
- **Dockerized** — One-command setup, no Python environment hassle
- **REST API** — Simple HTTP endpoints for easy integration
- **Multiple Audio Formats** — MP3, WAV, WebM, M4A, MP4, and more
- **Segmented Output** — Time-stamped transcription segments available
- **CORS Enabled** — Ready for frontend integration
- **Model Caching** — Docker volume persists downloaded models

---

## 📋 Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)
- ~2 GB disk space for the model
- Minimum 4 GB RAM (8 GB recommended)

---

## 🚀 Quick Start

### 1. Clone this repository

```bash
git clone https://github.com/alamin5g/bangla-stt.git
cd bangla-stt
```

### 2. Start the service

```bash
docker compose up -d --build
```

> ⏳ First run: The model (~1 GB) will be downloaded from HuggingFace. This takes 2-10 minutes depending on your internet speed. Subsequent runs use the cached model.

### 3. Test it

```bash
# Health check
curl http://localhost:5000/health

# Transcribe an audio file
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@your_bangla_audio.wav"
```

**Expected output:**

```json
{
  "success": true,
  "text": "রহিম মিয়া দশ কেজে চাউল বাকী নিয়েছে, তার মোট বিল হয়েছে আঠারো সত্ত্বর টাকা।"
}
```

That's it! Your Bangla STT service is running on `http://localhost:5000`. 🎉

---

## 📁 Project Structure

```
bangla-stt/
├── app.py                  # Flask REST API server
├── Dockerfile              # Python 3.10 + dependencies
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

---

## 🔌 API Endpoints

### `GET /health`

Health check endpoint to verify the service is running.

**Response:**

```json
{
  "status": "healthy"
}
```

---

### `POST /transcribe`

Transcribe a Bangla audio file to text.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `audio` (file) — Supported formats: MP3, WAV, WebM, M4A, MP4

```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@recording.wav"
```

**Response:**

```json
{
  "success": true,
  "text": "বাংলায় বলা কথা এখানে আসবে"
}
```

**Error Response:**

```json
{
  "error": "No audio file provided"
}
```

---

### `POST /transcribe/segments`

Transcribe audio with time-stamped segments (useful for subtitle generation).

**Request:** Same as `/transcribe`

```bash
curl -X POST http://localhost:5000/transcribe/segments \
  -F "audio=@recording.wav"
```

**Response:**

```json
{
  "success": true,
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "রহিম মিয়া দশ কেজে চাউল"
    },
    {
      "start": 2.5,
      "end": 5.0,
      "text": "বাকী নিয়েছে"
    }
  ]
}
```

---

## ⚙️ Configuration

### Model Size

Edit the `MODEL_SIZE` environment variable in `docker-compose.yml` to change the model:

```yaml
environment:
  - MODEL_SIZE=small   # Options: tiny, base, small, large
```

| Model | Size | WER | Best For | RAM Required |
|-------|------|-----|----------|-------------|
| `tiny` | 100-200 MB | 74 | Testing, low-resource | 1-2 GB |
| `base` | 200-300 MB | 46 | Quick prototyping | 2-4 GB |
| `small` | ~1 GB | 18 | Production (balanced) | 4-8 GB |
| `large` | 3-4 GB | 11 | Best accuracy | 8-16 GB |

> **Lower WER = Better accuracy.** For most use cases, `small` is the recommended choice.

### Port

Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "5000:5000"   # Change "5000:" to your preferred port
```

---

## 🔧 Docker Commands Reference

| Command | Description |
|---------|-------------|
| `docker compose up -d --build` | Build and start the service |
| `docker compose down` | Stop and remove the container |
| `docker compose restart` | Restart the service |
| `docker compose ps` | Check container status |
| `docker compose logs -f bangla-stt` | View live logs |
| `docker compose logs bangla-stt --tail 50` | Last 50 log lines |

---

## 🔗 Integration with Java SpringBoot

This Docker service is designed to work as a backend microservice. Your SpringBoot application connects to it via HTTP:

### SpringBoot Configuration (`application.yml`)

```yaml
server:
  port: 8080

bangla-stt:
  service-url: http://localhost:5000
  connect-timeout: 30000
  read-timeout: 120000
```

### SpringBoot Service Example

```java
@Service
public class BanglaSTTService {

    private final RestTemplate restTemplate;
    private final String serviceUrl;

    public String transcribe(MultipartFile audioFile) {
        String url = serviceUrl + "/transcribe";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("audio", new ByteArrayResource(audioFile.getBytes()) {
            @Override
            public String getFilename() {
                return audioFile.getOriginalFilename();
            }
        });

        HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);

        return (String) response.getBody().get("text");
    }
}
```

### Architecture

```
┌──────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Frontend │ ──── │  Java SpringBoot │ ──── │  Python (Docker) │
│ (Voice)  │      │    (Your API)    │      │  BanglaSpeech2Text│
└──────────┘      └──────────────────┘      └──────────────────┘
     │                    │                         │
   User records      Receives audio            Transcribes
   / uploads voice   → forwards to Python     → returns Bangla text
                      → receives text
                      → sends to frontend
```

---

## 🛠️ Troubleshooting

### Container fails to start / Model download fails

If the container can't reach HuggingFace to download the model, try using host networking:

```yaml
# docker-compose.yml
services:
  bangla-stt:
    build: .
    network_mode: host    # Use host's network
    volumes:
      - model_cache:/root/.cache/huggingface
    environment:
      - MODEL_SIZE=small
    restart: unless-stopped
```

### DNS resolution errors inside Docker

Add DNS servers to Docker's configuration:

```bash
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

```json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

```bash
sudo systemctl restart docker
docker compose down
docker compose up -d --build
```

### Out of memory

If you get OOM errors, switch to a smaller model:

```yaml
environment:
  - MODEL_SIZE=tiny   # Uses less RAM
```

Or increase Docker memory limit in Docker Desktop settings.

### Slow transcription

- Use `small` or `tiny` model instead of `large`
- If you have a NVIDIA GPU, install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for GPU acceleration

---

## 📊 Tech Stack

| Component | Technology |
|-----------|-----------|
| Speech Recognition | [BanglaSpeech2Text](https://github.com/shhossain/BanglaSpeech2Text) |
| ML Engine | [faster-whisper](https://github.com/guillaumekln/faster-whisper) (CTranslate2) |
| Base Model | OpenAI Whisper (fine-tuned for Bangla) |
| REST Framework | Flask + Gunicorn |
| Containerization | Docker + Docker Compose |
| Python | 3.10 |

---

## 📄 License

This project uses [BanglaSpeech2Text](https://github.com/shhossain/BanglaSpeech2Text) which is licensed under **Apache 2.0**. Free for personal and commercial use.

---

## 🙏 Credits

- [BanglaSpeech2Text](https://github.com/shhossain/BanglaSpeech2Text) by [Shifat Hossain](https://github.com/shhossain)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) by Guillaume Klein
- [OpenAI Whisper](https://github.com/openai/whisper) by OpenAI

---

## 📮 Issues & Contributions

Found a bug or have a feature request? Open an [issue](https://github.com/your-username/bangla-stt-docker/issues). Pull requests are welcome!
