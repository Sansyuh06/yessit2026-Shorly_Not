FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose KMS (8000), Chat (8765), Dashboard (8501), Mobile (8080)
EXPOSE 8000 8765 8501 8080

CMD ["python", "start_all.py"]
