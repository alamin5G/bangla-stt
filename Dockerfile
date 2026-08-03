FROM python:3.10-slim
WORKDIR /app
# Install deps from requirements.txt so the pgvector embedder dep
# (sentence-transformers, plan §6.7) is included in the image.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "app:app"]
