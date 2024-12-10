# Usa l'immagine di base di Python
FROM python:3.9

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia il file requirements.txt da DataCollector nel container
COPY ./AlertNotifierSystem.py /app/
COPY ./requirements.txt /app/
# Installa le dipendenze
RUN pip install --no-cache-dir -r /app/requirements.txt

# Comando per avviare il servizio
CMD ["python", "AlertNotifierSystem.py"]