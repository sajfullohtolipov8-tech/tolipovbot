FROM python:3.9-slim

WORKDIR /app

# Установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY tolipov.py .

# Запускаем бота
CMD ["python", "tolipov.py"]
