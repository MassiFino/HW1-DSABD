from .db_connection import get_db_connection

#Ogni operazione di scrittura deve avere un oggetto comando dedicato che rappresenta i dati necessari per l'esecuzione
class SaveTickerDataCommand:
    def __init__(self, ticker, value, timestamp):
        self.ticker = ticker
        self.value = value
        self.timestamp = timestamp    
        
class WriteOperation:
    def SaveTicker(self,ticker, value, timestamp):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO TickerData (ticker, value, timestamp) VALUES (%s, %s, %s)", (ticker, value, timestamp))
            conn.commit()

        finally:
            conn.close()
            
             
class WriteService:
    def __init__(self):
        self.operation = WriteOperation()

    def handle_ticker_data(self, command: SaveTickerDataCommand):
        self.operation.SaveTicker(command.ticker, command.value, command.timestamp)
        print(f"Ticker {command.ticker} salvato con successo!")
        
            
        
   
