FROM python:3.13
WORKDIR /usr/local/app

# Копируем файлы в контейнер и устанавливаем зависимости
COPY datab/* ./datab/
COPY templates/* ./templates/
COPY app.py ./
RUN pip install --no-cache-dir flask

# Открываем нужный порт
EXPOSE 5000

# Создаём дб
RUN touch cafe.db

# Запускаем сервер
CMD ["python3", "app.py"]