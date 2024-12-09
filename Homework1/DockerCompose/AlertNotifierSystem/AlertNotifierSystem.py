from confluent_kafka import Consumer, KafkaException
import json
import smtplib
from email.mime.text import MIMEText
import requests

bot_token = "7587852566:AAH0pXlB_VHM-UW1BZwhed5A9WzQnvLd5y8"  # Token del bot
chat_id = "324775130"  # Usa il tuo chat_id qui 
app_password = 'pqhv svrd rius pxmi'


# Kafka configuration for consumer
consumer_config = {
    'bootstrap.servers': 'localhost:29092',  # Indirizzo del broker Kafka
    'group.id': 'alertNotifierGroup',  # ID del gruppo consumer per la gestione degli offset
    'auto.offset.reset': 'earliest',  # Inizia a leggere dall'offset più basso
    'enable.auto.commit': False  # Disabilita il commit automatico per la gestione manuale
}

consumer = Consumer(consumer_config)  # Inizializza il Kafka consumer
topic_to_consume = 'to-notifier'  # Topic da cui leggere messaggi
# Funzione per inviare notifiche tramite Telegram

def send_telegram_message(message):
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
        msg['From'] = 'dariooor.00@gmail.com'  # Sostituisci con il tuo indirizzo Gmail
        msg['To'] = to_email  # Imposta il destinatario

        # Configura il server SMTP di Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Avvia la connessione TLS
            server.login('dariooor.00@gmail.com', app_password)  # Login con Gmail App Password
            server.send_message(msg)  # Invia il messaggio
            print(f"Email inviata con successo a: {to_email}")
    except Exception as e:
        print(f"Errore nell'invio dell'email a {to_email}: {e}")

# Test manuale per verificare se l'email viene inviata
print("Esecuzione test manuale per verificare l'invio delle email...")
send_email(
    to_email='dario.r1208@gmail.com@',  # Modifica con il tuo indirizzo email
    subject='Test Email Manuale',
    body='Questo è un messaggio di test inviato manualmente per verificare la connessione Gmail SMTP.'
)
print("Test manuale completato.")
# Variabili di stato per memorizzare messaggi ricevuti
received_messages = []  # Buffer per memorizzare i messaggi in arrivo
message_count = 0  # Contatore per tracciare il numero di messaggi ricevuti

# Prova manuale per inviare un messaggio Telegram
print("\nEsecuzione test manuale per verificare l'invio di un messaggio Telegram...")
test_message = "🔔 Test manuale: Questo è un messaggio di prova Telegram!"
send_telegram_message(test_message)
print("Test manuale completato.\n")

# Sottoscrivi il consumer al topic desiderato
consumer.subscribe([topic_to_consume])

try:
    while True:
        # Poll per un nuovo messaggio dal topic Kafka
        msg = consumer.poll(1.0)  # Aspetta fino a 1 secondo per un messaggio
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
        received_messages.append(data)  # Memorizza il messaggio ricevuto
        message_count += 1  # Incrementa il contatore di messaggi

        # Verifica che il messaggio contenga le informazioni necessarie
        if 'email' in data and 'ticker' in data and 'condition' in data:
            # Prepara il messaggio email
            subject = f"Alert per {data['ticker']}"
            body = (
                f"Salve,\n\n"
                f"Il ticker '{data['ticker']}' ha attivato la seguente condizione:\n"
                f"{data['condition']}\n"
                f"Valore più recente: {data['latest_value']}\n\n"
                f"Distinti saluti,\nSistema di Notifiche Alert"
            )
            # Invia l'email al destinatario
            send_email(data['email'], subject, body)
             # Invia anche la notifica Telegram
            telegram_message = (
                f"🚀 Alert: Il ticker '{data['ticker']}' ha attivato la seguente condizione:\n"
                f"{data['condition']}\n"
                f"Valore più recente: {data['latest_value']}"
            )
            send_telegram_message(telegram_message)
        else:
            print("Dati incompleti ricevuti. Salto del messaggio.")

        # Commette l'offset manualmente per garantire che il messaggio venga processato solo una volta
        consumer.commit(asynchronous=False)
        print(f"Offset commesso per il messaggio: {msg.offset()}")

except KeyboardInterrupt:
    # Interruzione pulita del consumer
    print("\nConsumer interrotto dall'utente.")
finally:
    # Chiudi il consumer quando l'app termina
    consumer.close()
    print("Consumer di Kafka chiuso.")
