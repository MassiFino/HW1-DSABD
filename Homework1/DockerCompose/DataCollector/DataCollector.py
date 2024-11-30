import os
from datetime import datetime
import mysql.connector
import yfinance as yf
import time
from circuit import CircuitBreaker, CircuitBreakerOpenException

# Configurazione del Circuit Breaker
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)


db_config = {
    'user': 'root',
    'password': '1234',
    'host': 'db',  # Questo è l'hostname del tuo database nel Docker Compose
    'database': 'yfinance_db',  # Il nome del database che hai creato nel tuo Docker Compose
    'port': 3306,
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except mysql.connector.Error as err:
        print(f"Errore durante la connessione al database: {err}")
        return None


def get_tickers():
    """
    Recupera ticker associati dal database.
    :return: Lista di tuple (ticker).
    """
    conn = get_db_connection()
    if not conn.is_connected():
        raise Exception("[Errore] Connessione al database fallita.")

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT ticker FROM Tickers")
        rows = cursor.fetchall()
        if not rows:
            print("[Info] Nessun utente registrato con tickers associati.")
            return []
        
        return [row[0] for row in rows]

    finally:
        conn.close()


def save_ticker_data(ticker, value, timestamp):
    """
    Salva i dati dei ticker recuperati nel database.
    :param ticker: Codice del titolo azionario.
    :param value: Valore del titolo.
    :param timestamp: Timestamp corrente.
    """
    conn = get_db_connection()
    if not conn.is_connected():
        raise Exception("[Errore] Connessione al database fallita.")

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO TickerData (ticker, value, timestamp) VALUES (%s, %s, %s)", (ticker, value, timestamp))
        conn.commit()
    finally:
        conn.close()

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
        # Proteggi l'intera chiamata a yfinance, inclusi i dati storici e il prezzo corrente
        stock_price = get_stock_price(ticker)
        timestamp = datetime.now()
        save_ticker_data(ticker, stock_price, timestamp)
        print(f"Dati salvati per {ticker}: {stock_price} @ {timestamp}")
    except Exception as e:
        print(f"[Errore] Elaborazione fallita per {ticker}: {e}")


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


if __name__ == "__main__":
    print("[Info] Avvio del programma per l'aggiornamento dei ticker ogni 5 minuti.")
    while True:
        run()
        print("[Info] Attesa di 5 minuti prima del prossimo aggiornamento.")
        time.sleep(300)