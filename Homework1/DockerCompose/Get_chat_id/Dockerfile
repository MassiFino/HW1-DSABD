# Usa un'immagine base di Python
FROM python:3.9

WORKDIR /app

COPY ./getChatId.py /app/
COPY ./requirements.txt /app/

COPY ./CQRS_Pattern /app/CQRS_Pattern/


RUN pip install --no-cache-dir -r requirements.txt

# Comando per eseguire lo script
CMD ["python", "getChatId.py"]
