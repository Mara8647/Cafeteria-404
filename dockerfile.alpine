FROM alpine:latest

RUN mkdir /app
WORKDIR /app

# Копируем файлы в контейнер и устанавливаем зависимости
COPY datab/* ./datab/
COPY templates/* ./templates/
COPY app.py ./

# Устанавливаем все необходимые зависимости
RUN apk add python3 py3-pip
RUN pip install --break-system-packages flask

# Открываем нужный порт
EXPOSE 5000

# Создаём дб
RUN touch cafe.db

# Запускаем сервер
CMD ["python3", "app.py"]