from .db_connection import get_db_connection

#Ogni operazione di scrittura deve avere un oggetto comando dedicato che rappresenta i dati necessari per l'esecuzione
class RegisterUserCommand:
    def __init__(self, email, ticker, max_value, min_value):
        self.email = email
        self.ticker = ticker
        self.max_value = max_value
        self.min_value = min_value

class UpdateUserCommand:
    def __init__(self, email, ticker_old, ticker, max_value, min_value):
        self.email = email
        self.ticker_old = ticker_old
        self.ticker = ticker
        self.max_value = max_value
        self.min_value = min_value
        
class DeleteTickerUserCommand:
    def __init__(self, email, ticker):
        self.email = email
        self.ticker = ticker
        
class DeleteUserCommand:
    def __init__(self, email):
        self.email = email
        
class AddTickerCommand:
    def __init__(self, email, ticker, max_value, min_value):
        self.email = email
        self.ticker = ticker
        self.max_value = max_value
        self.min_value = min_value  
              
class UpdateMinMaxValueCommand:
    def __init__(self, email, ticker, max_value, min_value):
        self.email = email
        self.ticker = ticker
        self.max_value = max_value
        self.min_value = min_value        
        
class WriteOperation:
    def register_user(self, email, ticker, max_value, min_value):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        
        try:
            cursor = conn.cursor()
            
            # Inserisce l'utente se non esiste
            cursor.execute("SELECT email FROM Users WHERE email = %s", (email,))
            if cursor.fetchone() is not None:
                raise Exception(f"Email: {email} già presente nel database")
                    
            cursor.execute("INSERT INTO Users (email) VALUES (%s)", (email,))
            
            # Inserisce il ticker se non esiste
            cursor.execute("SELECT ticker FROM Tickers WHERE ticker = %s", (ticker,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO Tickers (ticker) VALUES (%s)", (ticker,))
            
            # Associa l'utente al ticker
            cursor.execute("""
                INSERT INTO UserTickers (user, ticker, max_value, min_value)
                VALUES (%s, %s, %s, %s)
            """, (email, ticker, max_value, min_value))

            conn.commit()
        finally:
            conn.close()
            
    def update_user(self, email, ticker_old, ticker, max_value, min_value):
            conn = get_db_connection()
            if conn is None:
                raise Exception("Errore durante la connessione al database!")
            try:

                cursor =  conn.cursor()
    
                cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s", (email,))
                rows = cursor.fetchall()  # Recupera tutte le righe associate all'utente

                # Controllo se ticker_old è presente tra i tickers associati all'utente
                tickers = [row[0] for row in rows] 
                if ticker_old not in tickers:
                    raise Exception(f"Ticker: {ticker_old} non trovato per l'utente {email}")
                # Controllo se ticker è già associato
                if ticker in tickers:
                    raise Exception(f"Ticker: {ticker_old} è già associato all'utente {email}")
  
                cursor.execute("SELECT ticker FROM Tickers WHERE ticker = %s", (ticker,))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO Tickers (ticker) VALUES (%s)", (ticker,))

                cursor.execute("UPDATE UserTickers SET ticker = %s, max_value = %s, min_value = %s WHERE user = %s AND ticker = %s", (ticker,max_value,min_value, email,ticker_old))

                cursor.execute("SELECT COUNT(*) FROM UserTickers WHERE ticker = %s", (ticker_old,))
                count = cursor.fetchone()[0]  # Ottieni il numero di associazioni

                if count == 0:  # Se non ci sono altre associazioni
                    # Elimina il ticker dalla tabella Tickers
                    cursor.execute("DELETE FROM Tickers WHERE ticker = %s", (ticker_old,))

                conn.commit()
            finally:
                conn.close()
                
    def delete_ticker_user(self,email, ticker):
            conn = get_db_connection()
            if conn is None:
                raise Exception("Errore durante la connessione al database!")
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (email, ticker))

                if cursor.fetchone() is None:
                    raise(f"{ticker} non trovato per l'utente {email}")
                cursor.execute("DELETE FROM UserTickers WHERE user = %s AND ticker = %s", (email, ticker))
                cursor.execute("SELECT COUNT(*) FROM UserTickers WHERE ticker = %s", (ticker,))
                count = cursor.fetchone()[0]
                if count == 0:  # Se non è associato a nessun altro utente
                    cursor.execute("DELETE FROM Tickers WHERE ticker = %s", (ticker,))
                conn.commit()
            finally:
                conn.close()
                
    def delete_user(self,email):    
            conn = get_db_connection()
            if conn is None:
                raise Exception("Errore durante la connessione al database!")
            try:
                cursor = conn.cursor()
                cursor.execute("Select ticker FROM UserTickers WHERE user = %s", (email,))
                rows = cursor.fetchall()
                tickers = [row[0] for row in rows]  # row[0] contiene il valore di "ticker"
                cursor.execute("DELETE FROM Users WHERE email = %s", (email,))
                for ticker in tickers:
                    cursor.execute("SELECT COUNT(*) FROM UserTickers WHERE ticker = %s", (ticker,))
                    count = cursor.fetchone()[0]
                if count == 0:  # Se non è associato a nessun altro utente
                    cursor.execute("DELETE FROM Tickers WHERE ticker = %s", (ticker,))
                conn.commit()
            finally:
                conn.close()
    def add_ticker(self,email, ticker,max_value,min_value):    
            conn = get_db_connection()
            if conn is None:
                raise Exception("Errore durante la connessione al database!")
            try:
                cursor = conn.cursor()
                #controllo se l'utente ha già quel ticker
                cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (email, ticker))
                if cursor.fetchone() is not None:
                    raise(f"Ticker {ticker} già presente per l'utente {email}!")
                cursor.execute("SELECT ticker FROM Tickers WHERE ticker = %s", (ticker,))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO Tickers (ticker) VALUES (%s)", (ticker,))
                    cursor.execute("INSERT INTO UserTickers (user, ticker, max_value, min_value) VALUES (%s, %s, %s, %s)", (email, ticker, max_value, min_value))
                conn.commit()
            finally:
                conn.close()
                
    def update_min_max_value(self, email,ticker, max_value, min_value):
        conn = get_db_connection()
        if conn is None:
            raise Exception(f"Errore durante la connessione al database!")
        
        try: 
            cursor = conn.cursor()
            cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (email,ticker))

            row = cursor.fetchone()

            if row is None:
                raise Exception(f"Non hai questo ticker tra quelli di interesse, codice ticker")
        
            #prima di modificare controllo se i valori inseriti sono uguali a quelli già presenti
            cursor.execute("SELECT max_value, min_value FROM UserTickers WHERE user = %s AND ticker = %s", (email, ticker))
            row = cursor.fetchone()
            if row[0] == max_value and row[1] == min_value:     
                raise Exception(f"I valori inseriti sono uguali a quelli già presenti")
            cursor.execute("UPDATE UserTickers SET max_value = %s, min_value = %s WHERE user = %s AND ticker = %s", (max_value, min_value, email, ticker))   
            conn.commit()
        finally:
                conn.close()   
             
class WriteService:
    def __init__(self):
        self.operation = WriteOperation()

    def handle_register_user(self, command: RegisterUserCommand):
        self.operation.register_user(command.email, command.ticker, command.max_value, command.min_value)
        print(f"Utente {command.email} registrato con successo con il ticker {command.ticker}!")
        
    def handle_update_user(self,command:UpdateUserCommand):
        self.operation.update_user(command.email, command.ticker_old, command.ticker, command.max_value,command.min_value)
        print(f"Utente {command.email} aggiornato con successo con il nuovo ticker{command.ticker}!")
    
    def handle_delete_ticker_user(self,command:DeleteTickerUserCommand):
        self.operation.delete_ticker_user(command.email, command.ticker)
        print(f"tikcer {command.ticker} dell'utente {command.email} eliminato con successo!")
        
       
    def handle_delete_user(self,command:DeleteUserCommand):
        self.operation.delete_user(command.email)
        print(f"Utente {command.email} eliminato con successo!")
    
    def handle_addTicker(self,command:AddTickerCommand):
        self.operation.add_ticker(command.email, command.ticker,command.max_value,command.min_value)
        print(f"Aggiunto ticker {command.ticker} all'utente {command.email} !")
    
    def handle_update_min_max_value(self,command:UpdateMinMaxValueCommand):
        self.operation.update_min_max_value(command.email, command.ticker, command.max_value,command.min_value)
        print(f"Utente {command.email} aggiornato con successo con il nuovo ticker{command.ticker}!")
        
            
        
   
