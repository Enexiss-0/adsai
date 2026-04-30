FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends gcc \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY backend.py index.html styles.css app.js users.json .gitignore ./

EXPOSE 5000
CMD ["python", "backend.py"]
