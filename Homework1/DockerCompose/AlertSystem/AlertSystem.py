from datetime import datetime
import mysql.connector
from confluent_kafka import Consumer, Producer, KafkaException
import json


# Kafka configuration for consumer and producer
consumer_config = {
    'bootstrap.servers': 'broker1:29092',  # Usa il nome del servizio del broker nel docker-compose
    'group.id': 'group1',  # Cambia il group.id per differenziare i consumatori se necessario
    'enable.auto.commit': False,
    'auto.offset.reset': 'earliest',  # Parte dal primo messaggio se non c'è offset salvato
}

producer_config = {
    'bootstrap.servers': 'broker1:29092',
    'acks': 'all', 
    'max.in.flight.requests.per.connection': 1,  # Only one in-flight request per connection
    'retries': 3  # Retry up to 3 times on failure
}  # Producer configuration


db_config = {
    'user': 'root',
    'password': '1234',
    'host': 'db',  # Questo è l'hostname del tuo database nel Docker Compose
    'database': 'yfinance_db',  # Il nome del database che hai creato nel tuo Docker Compose
    'port': 3306,
}


values = []


consumer = Consumer(consumer_config)
producer = Producer(producer_config)

topic1 = 'to-alert-system'  
topic2 = 'to-notifier'



consumer.subscribe([topic1])


def produce_sync(producer, topic, value):
    try:
        producer.produce(topic, value)
        producer.flush()  
        print(f"Synchronously produced message to {topic}: {value}")
    except Exception as e:
        print(f"Failed to produce message: {e}")



def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except mysql.connector.Error as err:
        print(f"Errore durante la connessione al database: {err}")
        return None
    

while True:
    # Consuma un messaggio da Kafka
    msg = consumer.poll(300.0)  # Tempo massimo di attesa in secondi
    
    if msg is None:
        # Nessun messaggio disponibile, riprova
        print("Nessun messaggio ricevuto. Continuo ad aspettare...")
        continue  
    
    if msg.error():
        # Gestisce eventuali errori durante il consumo
        if msg.error().code() == KafkaException._PARTITION_EOF:
            print(f"Fine della partizione raggiunta {msg.topic()} [{msg.partition()}]")
        else:
            print(f"Errore del consumer: {msg.error()}")
        continue  # Salta al prossimo ciclo
    
    try:
        # Decodifica il messaggio
        data = json.loads(msg.value().decode('utf-8'))
        print(f"Received: {data}")
        
        # Connessione al database
        conn = get_db_connection()
        if not conn:
            print("Errore nella connessione al database. Salto il messaggio.")
            continue  # Salta al prossimo ciclo
        
        # Esegui la query sul database
        cursor = conn.cursor()
        query = """
        SELECT 
            u.email,
            u.chat_id,
            ut.ticker,
            td.value AS latest_value,
            CASE 
                WHEN ut.min_value > 0 AND td.value < ut.min_value THEN CONCAT('Sotto Min Value: ', ut.min_value)
                WHEN ut.max_value > 0 AND td.value > ut.max_value THEN CONCAT('Sopra Max Value: ', ut.max_value)
            END AS condition
        FROM 
            UserTickers ut
        JOIN 
            TickerData td ON ut.ticker = td.ticker
        JOIN 
            Users u ON ut.user = u.email
        WHERE 
            td.timestamp = (SELECT MAX(timestamp) FROM TickerData WHERE ticker = ut.ticker)
            AND (
                (ut.min_value > 0 AND td.value < ut.min_value) OR
                (ut.max_value > 0 AND td.value > ut.max_value)
            );
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        for row in results:
            messaggio = {
                "email": row["email"],
                "chat_id": row["chat_id"],
                "ticker": row["ticker"],
                "condition": row["condition"],
                "latest_value": row["latest_value"],
            }
            values.append(messaggio)

        cursor.close()
        conn.close()
        
        # Produce il messaggio su Kafka
        produce_sync(producer, topic2, json.dumps(values))

        # Commit dell'offset
        consumer.commit(asynchronous=False)
        print(f"Committed offset for message: {msg.offset()}")
        
        values = []  # Resetta la lista dei messaggi
    
    except Exception as e:
        # Gestisce eventuali eccezioni durante l'elaborazione
        print(f"Errore durante l'elaborazione del messaggio: {e}")
    finally:
        consumer.close()
        print("Consumer chiuso correttamente.")

