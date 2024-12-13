from confluent_kafka import Consumer, KafkaException
import json
import smtplib
from email.mime.text import MIMEText
import requests

bot_token = "7587852566:AAH0pXlB_VHM-UW1BZwhed5A9WzQnvLd5y8"  # Token del bot
chat_id = "324775130"  # Usa il tuo chat_id qui 
app_password = 'hymj pfrc fzha zetl'


# Kafka configuration for consumer
consumer_config = {
    'bootstrap.servers': 'broker1:29092',  # Usa il nome del servizio del broker nel docker-compose
    'group.id': 'group2',
    'enable.auto.commit': False,
    'auto.offset.reset': 'earliest',  # Parte dal primo messaggio se non c'è offset salvato
}

consumer = Consumer(consumer_config)  # Inizializza il Kafka consumer
topic_to_consume = 'to-notifier'  # Topic da cui leggere messaggi
# Funzione per inviare notifiche tramite Telegram

def send_telegram_message(message, chat_id):
    """Invia un messaggio tramite Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Messaggio Telegram inviato con successo!")
        else:
            print("Errore nell'invio del messaggio Telegram:", response.json())
    except Exception as e:
        print("Errore nella connessione con Telegram:", e)
        
        
# Funzione per inviare email tramite Gmail SMTP
def send_email(to_email, subject, body):
    try:
        # Crea il messaggio email
        msg = MIMEText(body)  # Imposta il corpo dell'email
        msg['Subject'] = subject  # Imposta l'oggetto
        msg['From'] = 'hwdsbd@gmail.com'  # Sostituisci con il tuo indirizzo Gmail
        msg['To'] = to_email  # Imposta il destinatario

        # Configura il server SMTP di Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Avvia la connessione TLS
            server.login('hwdsbd@gmail.com', app_password)  # Login con Gmail App Password
            server.send_message(msg)  # Invia il messaggio
            print(f"Email inviata con successo a: {to_email}")
    except Exception as e:
        print(f"Errore nell'invio dell'email a {to_email}: {e}")

# Variabili di stato per memorizzare messaggi ricevuti
received_messages = []  # Buffer per memorizzare i messaggi in arrivo

# Sottoscrivi il consumer al topic desiderato
consumer.subscribe([topic_to_consume])

try:
    while True:
        # Poll per un nuovo messaggio dal topic Kafka
        msg = consumer.poll(300.0)  # Aspetta fino a 5 minutinper un messaggio
        if msg is None:
            # Nessun messaggio ricevuto entro il tempo di polling
            continue
        if msg.error():
            # Gestione di errori durante il consumo
            if msg.error().code() == KafkaException._PARTITION_EOF:
                print(f"Fine della partizione raggiunta: {msg.topic()} [{msg.partition()}]")
            else:
                print(f"Errore del consumer: {msg.error()}")
            continue

        # Decodifica il messaggio ricevuto (assunto JSON)
        data = json.loads(msg.value().decode('utf-8'))

        received_messages.append(data)  # Add the parsed message to the buffer

        # Commette l'offset manualmente per garantire che il messaggio venga processato solo una volta
        consumer.commit(asynchronous=False)
        print(f"Offset commesso per il messaggio: {msg.offset()}")

        # Verifica che il messaggio sia una lista di dizionari
        if isinstance(received_messages, list):
            for item in data:
                # Verifica che l'elemento contenga le informazioni necessarie
                if 'email' in item and 'ticker' in item and 'condition' in item and 'latest_value' in item:
                    # Prepara l'email per l'utente
                    subject = f"Alert per {item['ticker']}"
                    body = (
                        f"Salve,\n\n"
                        f"Il ticker '{item['ticker']}' ha attivato la seguente condizione:\n"
                        f"{item['condition']}\n"
                        f"Valore più recente: {item['latest_value']}\n\n"
                        f"Distinti saluti,\nSistema di Notifiche Alert"
                    )
                    # Invia l'email
                    send_email(item['email'], subject, body)

                    # Prepara e invia la notifica Telegram (se chat_id è presente)
                    if 'chat_id' in item and item['chat_id']:
                        telegram_message = (
                            f"🚀 Alert: Il ticker '{item['ticker']}' ha attivato la seguente condizione:\n"
                            f"{item['condition']}\n"
                            f"Valore più recente: {item['latest_value']}"
                        )
                        send_telegram_message(telegram_message, item['chat_id'])

                    received_messages = []
                else:
                    print(f"Elemento incompleto ricevuto: {item}")
        else:
            print("Messaggio ricevuto non è una lista. Ignorato.")

except KeyboardInterrupt:
    # Interruzione pulita del consumer
    print("\nConsumer interrotto dall'utente.")
finally:
    # Chiudi il consumer quando l'app termina
    consumer.close()
    print("Consumer di Kafka chiuso.")
