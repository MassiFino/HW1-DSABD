from .db_connection import get_db_connection


class ReadService:
    def login_user(self,email):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM Users WHERE email = %s", (email,))
            result=cursor.fetchone()
            if  result is None:
                raise Exception(f"{email} non è registrata")
            return result
        finally:
           conn.close()
            
    def show_ticker_user(self, email):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        try:
            cursor = conn.cursor()
            #controllo se l'utente ha già quel ticker
            cursor.execute("SELECT ticker, max_value, min_value FROM UserTickers WHERE user = %s", (email,))
            ticker= cursor.fetchall()
            if not ticker:
               raise Exception(f"L'utente {email} non ha alcun ticker da visualizzare")
            tickers_list = "\n".join([row[0] for row in ticker])
            return tickers_list
        finally:
           conn.close()
           
    def get_latest_value(self,email,ticker):
        conn = get_db_connection()
        if conn is None:
            raise Exception(f"Errore durante la connessione al database!")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Ticker FROM UserTickers WHERE user = %s AND ticker = %s", (email,ticker))
            row = cursor.fetchone() 
            if row is None:
                raise Exception(f"Non hai questo ticker tra quelli di interesse, codice ticker")
           
            tick= row[0]
        
            cursor.execute("SELECT value, timestamp FROM TickerData WHERE ticker = %s ORDER BY timestamp DESC LIMIT 1", (tick,))

            result = cursor.fetchone()
        
            if result is None:                
                raise Exception(f"Non è stato ancora aggiornato il ticker per {tick}")
        
              # Se result non è None, procedi con l'unpacking
            stock_value, timestamp = result
            if stock_value is None:
                raise Exception(f"Non abbiamo valori per il ticker: {ticker}")

            datetime_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

           
            return stock_value, datetime_str
        finally:
            conn.close()
           
           
           
    def get_average_value(self,email,ticker,num_values):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        try:
        
            cursor = conn.cursor()
            cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (email,ticker))

            row = cursor.fetchone()

            if row is None:
                raise Exception(f"Non hai questo ticker tra quelli di interesse, codice ticker")

            ticker = row[0]
        
            cursor.execute("SELECT AVG(value), MAX(timestamp) FROM TickerData WHERE ticker = %s ORDER BY timestamp DESC LIMIT %s", (ticker,num_values))

            result = cursor.fetchone()

            if result[0] is None and result[1] is None:
               raise Exception( "Non è stato ancora aggiornato il ticker")

            media_valori, timestamp = result
        
            datetime_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

            if media_valori is None:
                raise Exception("Non abbiamo valori per il ticker")
        
            return media_valori,datetime_str
          
        finally:
           conn.close()