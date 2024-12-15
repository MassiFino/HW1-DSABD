import os
from datetime import datetime
import mysql.connector
import yfinance as yf
import time
from circuit import CircuitBreaker, CircuitBreakerOpenException
from confluent_kafka import Producer
import json
import CQRS_Pattern.lecture_db as lecture_db
import CQRS_Pattern.command_db as command_db

# Configurazione del Circuit Breaker
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)


producer_config = {
    'bootstrap.servers': 'broker1:29092',  # Kafka broker address
    'acks': 'all',  # Ensure all in-sync replicas acknowledge the message
    'max.in.flight.requests.per.connection': 1,  # Only one in-flight request per connection
    'retries': 3,  # Retry up to 3 times on failure
    'linger.ms':5 #attendiamo 5 secondi prima di mandare il batch successivo
}

producer = Producer(producer_config)
topic = 'to-alert-system'


def get_tickers():
    """
    Recupera ticker associati dal database.
    :return: Lista di tuple (ticker).
    """
    read_service = lecture_db.ReadService()

    try:
        tickers = read_service.ShowTicker()
        return tickers
    except Exception as e:
        print(f"[Errore] Recupero ticker fallito: {e}")
        return []


def save_ticker_data(ticker, value, timestamp):
    """
    Salva i dati dei ticker recuperati nel database.
    :param ticker: Codice del titolo azionario.
    :param value: Valore del titolo.
    :param timestamp: Timestamp corrente.
    """
    command = command_db.SaveTickerDataCommand(ticker, value, timestamp)

    write_service = command_db.WriteService()

    try:
        write_service.handle_ticker_data(command)
    except Exception as e:
        print(f"[Errore] Salvataggio dati fallito: {e}")

# Funzione per Processare i Ticker con il Circuit Breaker

def get_stock_price(ticker):
    """
    Recupera l'ultimo valore disponibile per il titolo azionario specificato.
    :param ticker: Codice del titolo azionario.
    :return: Ultimo prezzo disponibile come float.
    """
    try:
        # Chiamata al metodo `history()` di yfinance protetta dal Circuit Breaker
        stock_data = yf.Ticker(ticker)
  
        history = circuit_breaker.call(stock_data.history, period="1d")
        if history.empty:
            print(f"Nessun dato disponibile per il ticker: {ticker}")
            return None

        # Ottieni il prezzo di chiusura più recente
        last_price = history['Close'].iloc[-1]
        return float(last_price)
    except CircuitBreakerOpenException:
        print(f"[Errore] Circuit breaker aperto. Operazione saltata per {ticker}.")
    except Exception as e:
        raise Exception(f" Recupero prezzo per {ticker} fallito: {e}")


def process_ticker(ticker):
    """
    Processa un singolo ticker per un utente.
    :param ticker: Codice del titolo azionario.
    """
    try:

        stock_price = get_stock_price(ticker)
        timestamp = datetime.now()
        save_ticker_data(ticker, stock_price, timestamp)
        print(f"Dati salvati per {ticker}: {stock_price} @ {timestamp}")
    except Exception as e:
        print(f"[Errore] Elaborazione fallita per {ticker}: {e}")

def delivery_report(err, msg):
    """Callback to report the result of message delivery."""
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def produce_async(producer, topic):

    while True:
    # Generate a random value following a normal distribution
        timestamp = datetime.now().isoformat() 
        message = {'timestamp': timestamp, 'msg': 'aggiornamento valori completato'} 
        
        # Produce the message to TOPIC1
        #la callback serve per sapere se il messaggio è stato inviato correttamente in modo asincrono
        producer.produce(topic, json.dumps(message), callback=delivery_report)
        producer.flush()
        print(f"Produced: {message}")
        break


def run():
    """
    Processo principale:
    - Recupera utenti e ticker dal database.
    - Per ogni ticker, scarica i dati.
    - Salva i dati nel database.
    """
    try:
        tickers = get_tickers()
        if not tickers:
            print("[Info] Nessun dato da processare.")
            return

        for ticker in tickers:
            process_ticker(ticker)

        print("[Info] Aggiornamento completato.")

    except Exception as e:
        print(f"[Errore] Errore generale durante l'esecuzione: {e}")

    produce_async(producer, topic)


if __name__ == "__main__":
    print("[Info] Avvio del programma per l'aggiornamento dei ticker ogni 5 minuti.")
    while True:
        run()
        print("[Info] Attesa di 5 minuti prima del prossimo aggiornamento.")
        time.sleep(300)
