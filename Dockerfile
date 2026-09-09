FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY instagram_reporter_bot.py .

CMD ["python", "instagram_reporter_bot.py"]
