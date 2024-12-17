from datetime import datetime
from confluent_kafka import Consumer, Producer, KafkaException
import json
import CQRS_Pattern.lecture_db as lecture_db


# Kafka configuration for consumer and producer
consumer_config = {
    'bootstrap.servers': 'broker1:9092,broker2:9092,broker3:9092',  # Tre broker Kafka
    'group.id': 'group1',  # Cambia il group.id per differenziare i consumatori se necessario
    'enable.auto.commit': False,
    'auto.offset.reset': 'earliest',  # Parte dal primo messaggio se non c'è offset salvato
}


producer_config = {
    'bootstrap.servers': 'broker1:9092,broker2:9092,broker3:9092',  # Tre broker Kafka
    'acks': 'all',  # Ensure all in-sync replicas acknowledge the message
    'max.in.flight.requests.per.connection': 1,  # Ensure ordering of messages
    'batch.size': 500,  # Maximum size of a batch in bytes
    'retries': 3  # Number of retries for failed messages
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

    

try:
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

            # Esegue la query per ottenere i valori da notificare
            read_service = lecture_db.ReadService()

            results = read_service.NotifierValues()
            
            for row in results:
                email = row[0]
                chat_id = row[1]
                ticker = row[2]
                latest_value = row[3]
                condition = row[4]

                messaggio = {
                    "email": email,
                    "chat_id": chat_id,
                    "ticker": ticker,
                    "condition": condition,
                    "latest_value": latest_value,
                }
                values.append(messaggio)
            
            print(values)

            # Produce il messaggio su Kafka
            produce_sync(producer, topic2, json.dumps(values))

            # Commit dell'offset
            consumer.commit(asynchronous=False)
            print(f"Committed offset for message: {msg.offset()}")

            values = []  # Resetta la lista dei messaggi

        except Exception as e:
            # Gestisce eventuali eccezioni durante l'elaborazione
            print(f"Errore durante l'elaborazione del messaggio: {e}")

except KeyboardInterrupt:
    # Permette l'interruzione manuale con Ctrl+C
    print("\nInterruzione manuale ricevuta. Chiudo il consumer.")

finally:
    # Chiusura pulita del consumer
    consumer.close()
    print("Consumer chiuso correttamente.")


