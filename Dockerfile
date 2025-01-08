FROM python:3.12-slim

# Устанавливаем переменные окружения
ENV FLASK_APP=app.py

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y curl && \
    pip install --no-cache-dir -r requirements.txt

# Экспонируем порт
EXPOSE 5000

# Запускаем приложение
CMD ["flask", "run", "--host=0.0.0.0"]

