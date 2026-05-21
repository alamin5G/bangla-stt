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
- ~6 GB disk space (Docker image ~5.5 GB + model cache 200 MB – 4 GB depending on model size)
- Minimum 4 GB RAM (8 GB recommended for `large` model)

---

## 🚀 Quick Start

### 1. Clone this repository

```bash
git clone https://github.com/alamin5g/bangla-stt.git
cd bangla-stt
```

### 2. Build the Docker image

> ⚠️ **Important:** Due to BuildKit DNS resolution issues on some Linux systems, use `docker buildx` with `--network host` instead of `docker compose build`.

```bash
docker buildx build --network host -t bangla-stt .
```

### 3. Run the container

```bash
docker run -d --network host --name bangla-stt-container \
  -e MODEL_SIZE=small \
  -v bangla-stt_model_cache:/root/.cache/huggingface \
  --restart unless-stopped \
  bangla-stt
```

> 💡 After the first run, if you stop/restart your PC, the container auto-starts because of `--restart unless-stopped`. Docker must be running (`sudo systemctl start docker`).

To manually start/stop the container later:

```bash
docker start bangla-stt-container   # Start
docker stop bangla-stt-container    # Stop
```

### Alternative: Using Docker Compose

If `docker compose build` works on your system (no DNS issues):

```bash
docker compose up -d --build
```

> ⏳ First run: The model will be downloaded from HuggingFace. Download size depends on `MODEL_SIZE` — `small` is ~240 MB, `large` is ~3-4 GB. This takes 2-10 minutes depending on your internet speed. Subsequent runs use the cached model.

### 4. Test it

```bash
# Health check
curl http://localhost:5000/health

# Transcribe an audio file
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@test.wav"
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

| Model     | Size       | WER | Best For              | RAM Required |
| --------- | ---------- | --- | --------------------- | ------------ |
| `tiny`  | 100-200 MB | 74  | Testing, low-resource | 1-2 GB       |
| `base`  | 200-300 MB | 46  | Quick prototyping     | 2-4 GB       |
| `small` | ~1 GB      | 18  | Production (balanced) | 4-8 GB       |
| `large` | 3-4 GB     | 11  | Best accuracy         | 8-16 GB      |

> **Lower WER = Better accuracy.** For most use cases, `small` is the recommended choice.

### Port

The service uses `network_mode: host` by default, which means it runs directly on host port `5000`. To change the port, edit the `gunicorn` command in the `Dockerfile`:

```dockerfile
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", ...]
# Change 5000 to your preferred port
```

Alternatively, switch to port mapping by replacing `network_mode: host` in `docker-compose.yml`:

```yaml
ports:
  - "5000:5000"   # Change "5000:" to your preferred port
```

---

## 🔧 Docker Commands Reference

### Using `docker run` (recommended)

| Command | Description |
| ------- | ----------- |
| `docker buildx build --network host -t bangla-stt .` | Build the image (fixes BuildKit DNS issues) |
| `docker run -d --network host --name bangla-stt-container -e MODEL_SIZE=small -v bangla-stt_model_cache:/root/.cache/huggingface --restart unless-stopped bangla-stt` | Start the service |
| `docker start bangla-stt-container` | Start an existing container |
| `docker stop bangla-stt-container` | Stop the container |
| `docker logs -f bangla-stt-container` | View live logs |
| `docker logs bangla-stt-container --tail 50` | Last 50 log lines |
| `docker rm -f bangla-stt-container` | Force remove the container |
| `docker volume rm bangla-stt_model_cache` | Delete model cache (to free disk space) |

### Using Docker Compose (if DNS works on your system)

| Command | Description |
| ------- | ----------- |
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

### DNS resolution errors inside Docker (BuildKit `pip install` fails)

This is a known issue where Docker BuildKit cannot resolve DNS during `pip install`, even though the host machine has working internet. The error looks like:

```
ERROR: Could not find a version that satisfies the requirement banglaspeech2text
```

**Solution 1 (Recommended): Use `docker buildx` with host networking**

```bash
docker buildx build --network host -t bangla-stt .
docker run -d --network host --name bangla-stt-container \
  -e MODEL_SIZE=small \
  -v bangla-stt_model_cache:/root/.cache/huggingface \
  --restart unless-stopped \
  bangla-stt
```

**Solution 2: Add DNS to Docker daemon config**

```bash
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
```

Then restart:
```bash
sudo systemctl restart docker
docker compose down
docker compose up -d --build
```

> ⚠️ **Note:** Solution 2 may not work on all systems. If `docker compose build` still fails after adding DNS, use Solution 1 (`docker buildx build --network host`).

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

### Switching models or freeing disk space

To change the model size, you need to remove the old container and volume, then recreate with the new model:

```bash
# 1. Stop and remove the container
docker stop bangla-stt-container
docker rm bangla-stt-container

# 2. Delete the old model cache (frees disk space)
docker volume rm bangla-stt_model_cache

# 3. Start with new model size
docker run -d --network host --name bangla-stt-container \
  -e MODEL_SIZE=small \
  -v bangla-stt_model_cache:/root/.cache/huggingface \
  --restart unless-stopped \
  bangla-stt
```

> ⚠️ Deleting the volume means the new model must be re-downloaded on first run.

---

## 📊 Tech Stack

| Component          | Technology                                                                  |
| ------------------ | --------------------------------------------------------------------------- |
| Speech Recognition | [BanglaSpeech2Text](https://github.com/shhossain/BanglaSpeech2Text)            |
| ML Engine          | [faster-whisper](https://github.com/guillaumekln/faster-whisper) (CTranslate2) |
| Base Model         | OpenAI Whisper (fine-tuned for Bangla)                                      |
| REST Framework     | Flask + Gunicorn                                                            |
| Containerization   | Docker + Docker Compose                                                     |
| Python             | 3.10                                                                        |

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
