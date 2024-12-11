# Usa un'immagine base di Python
FROM python:3.9

WORKDIR /app

COPY ./getChatId.py /app/
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Comando per eseguire lo script
CMD ["python", "getChatId.py"]
