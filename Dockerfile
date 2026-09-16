FROM python:3.12-slim

WORKDIR /app

# Asılılıqları əvvəlcə kopyala - layer cache üçün (kod dəyişəndə asılılıqlar yenidən qurulmasın)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Qalan kodu kopyala
COPY . .

# Cloud Run PORT dəyişənini özü təyin edir (adətən 8080) - bunu tətbiq etmək vacibdir
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
