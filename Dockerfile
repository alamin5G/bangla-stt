FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir banglaspeech2text flask flask-cors gunicorn
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", \
     "--timeout", "120", "app:app"]
