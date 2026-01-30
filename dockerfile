FROM python:3.13
WORKDIR /usr/local/app

# Install the application dependencies
COPY datab/* ./datab/
COPY templates/* ./templates/
COPY app.py ./
RUN pip install --no-cache-dir flask

EXPOSE 5000

# Copy in the source code
RUN touch cafe.db

CMD ["python3", "app.py"]