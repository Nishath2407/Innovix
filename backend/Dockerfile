FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# Skip heavy ML deps in the base image build; install them separately if you
# want in-container emotion classification. The app falls back gracefully
# without them (see app/ai/emotion_service.py).
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "run:app"]
