import grpc
from concurrent import futures
import service_pb2, service_pb2_grpc
import mysql.connector
import mysql.connector.errors
from threading import Lock
from datetime import datetime
import CQRS_Pattern.command_db as command_db
#import CQRS_Pattern.query_db

cache = {
    "request_cache": {},
    "update_cache": {},
}

cache_lock = Lock()

identifier = None

class EchoService(service_pb2_grpc.EchoServiceServicer):
    # Configurazione del database (da usare con mysql.connector)
    db_config = {
        'user': 'root',
        'password': '1234',
        'host': 'db',  # Questo è l'hostname del tuo database nel Docker Compose
        'database': 'yfinance_db',  # Il nome del database che hai creato nel tuo Docker Compose
        'port': 3306,
    }

    def get_db_connection(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            if connection.is_connected():
                return connection
        except mysql.connector.Error as err:
            print(f"Errore durante la connessione al database: {err}")
            return None
    
    def LoginUser(self, request, context):
        "Login Utente"

        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.RegisterUserReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM Users WHERE email = %s", (request.email,))

        if cursor.fetchone() is None:

            return service_pb2.RegisterUserReply(
                success=False, 
                message=f"Email: {request.email} non è registrata"
            )
        
        
        global identifier
        identifier= request.email


        return service_pb2.RegisterUserReply(
                success=True, 
                message=f"Ti stiamo reindirizzando alla pagina principale"
            )


        

    def RegisterUser(self, request, context):
        """Metodo per registrare un utente."""
        meta = dict(context.invocation_metadata())

        userid = meta.get('userid', 'unknown')

        print(f"Richiesta di registrazione da: UserID: {userid}")

        with cache_lock:
            if userid in cache["request_cache"]:
                print(f"Risposta in cache per UserID {userid}")
                return cache["request_cache"][userid]
        

        cmd = command_db.RegisterUserCommand(
            email=request.email,
            ticker=request.ticker,
            max_value=request.max_value,
            min_value=request.min_value
        )

        write_service = command_db.WriteService()

        try:
            # Tenta di eseguire la logica di scrittura
            write_service.handle_register_user(cmd)
            
            global identifier
            identifier = request.email

            response = service_pb2.RegisterUserReply(
                success=True, 
                message=f"Utente {request.email} registrato con successo!"
            )

            with cache_lock:
                cache["request_cache"][userid] = response
            
            return response

        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response = service_pb2.RegisterUserReply(
                success=False,
                message=str(e)
            )
            with cache_lock:
                cache["request_cache"][userid] = response
            return response
        
    
    def UpdateUser(self, request, context):
        """Metodo per aggiornare il codice dell'azione dell'utente."""

        meta = dict(context.invocation_metadata())

        requestid = meta.get('requestid', 'unknown')

        print(f"Richiesta di aggionamento con RquestID: {requestid}")

        with cache_lock:
            if requestid in cache["update_cache"]:
                print(f"Risposta in cache per RequestID {requestid}")
                return cache["update_cache"][requestid]

        conn = self.get_db_connection()
        if conn is None:
            response = service_pb2.UpdateUserReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )

            with cache_lock:
                cache["update_cache"][requestid] = response
        
            return response


        
        cursor = conn.cursor()

        cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s", (identifier,))
        rows = cursor.fetchall()  # Recupera tutte le righe associate all'utente

        # Controllo se ticker_old è presente tra i tickers associati all'utente
        tickers = [row[0] for row in rows] 

        if request.ticker_old not in tickers:
            response = service_pb2.UpdateUserReply(
            success=False,
            message=f"Ticker: {request.ticker_old} non trovato per l'utente {identifier}"
            )
            with cache_lock:
                cache["update_cache"][requestid] = response
        
            return response

        if request.ticker in tickers:
            response = service_pb2.UpdateUserReply(
            success=False,
            message=f"Ticker: {request.ticker} è già associato all'utente {identifier}"
            )
            with cache_lock:
                cache["update_cache"][requestid] = response
        
            return response
        
        cursor.execute("SELECT ticker FROM Tickers WHERE ticker = %s", (request.ticker,))

        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO Tickers (ticker) VALUES (%s)", (request.ticker,))
            
        cursor.execute("UPDATE UserTickers SET ticker = %s, max_value = %s, min_value = %s WHERE user = %s AND ticker = %s", (request.ticker,request.max_value, request.min_value, identifier, request.ticker_old))

        cursor.execute("SELECT COUNT(*) FROM UserTickers WHERE ticker = %s", (request.ticker_old,))
        count = cursor.fetchone()[0]  # Ottieni il numero di associazioni

        if count == 0:  # Se non ci sono altre associazioni
        # Elimina il ticker dalla tabella Tickers
            cursor.execute("DELETE FROM Tickers WHERE ticker = %s", (request.ticker_old,))
            print(f"Ticker {request.ticker_old} eliminato perché non più associato ad altri utenti.")
        else:
            print(f"Ticker {request.ticker_old} è ancora associato a {count} utente/i.")

        conn.commit()
        conn.close()
        
        response = service_pb2.UpdateUserReply(
            success=True, 
            message=f"Codice dell'azione aggiornato per l'utente {identifier}!"
        )
        with cache_lock:
            cache["update_cache"][requestid] = response
        
        return response
        
    def DeleteTickerUser(self, request, context):
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.DeleteTickerUserReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )
        
        cursor = conn.cursor()
        ticker = request.ticker  # Ticker specifico da eliminare
        print(f"Utente: {identifier}, Ticker da eliminare: {ticker}")

        cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (identifier, ticker))

        if cursor.fetchone() is None:
            return service_pb2.DeleteTickerUserReply(
            success=False,
            message=f"Ticker: {request.ticker} non trovato per l'utente {identifier}"
            )
        
      
        cursor.execute("DELETE FROM UserTickers WHERE user = %s AND ticker = %s", (identifier, ticker))
        print(f"Ticker {ticker} eliminato dalla tabella UserTickers per l'utente {identifier}.")
        # Controllo se ticker_old è presente tra i tickers associati all'utente
        cursor.execute("SELECT COUNT(*) FROM UserTickers WHERE ticker = %s", (ticker,))
        count = cursor.fetchone()[0]
        if count == 0:  # Se non è associato a nessun altro utente
            cursor.execute("DELETE FROM Tickers WHERE ticker = %s", (ticker,))
            print(f"Ticker {ticker} eliminato perché non più associato ad altri utenti.")

        conn.commit()

        conn.close()
        
        return service_pb2.DeleteTickerUserReply(
        success=True,
        message=f"Ticker {request.ticker} eliminato con successo."
        )
       


    def DeleteUser(self, request, context):
        """Metodo per eliminare un utente."""
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.DeleteUserReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )

        
        print(f"email: {identifier}")
        
        cursor = conn.cursor()
        cursor.execute("Select ticker FROM UserTickers WHERE user = %s", (identifier,))
        rows = cursor.fetchall()

        tickers = [row[0] for row in rows]  # row[0] contiene il valore di "ticker"

        print(f"ticker: {tickers}")
    
        cursor.execute("DELETE FROM Users WHERE email = %s", (identifier,))

        print("siamo dopo l'eliminazione")

        for ticker in tickers:
            cursor.execute("SELECT COUNT(*) FROM UserTickers WHERE ticker = %s", (ticker,))
            count = cursor.fetchone()[0]

            if count == 0:  # Se non è associato a nessun altro utente
                cursor.execute("DELETE FROM Tickers WHERE ticker = %s", (ticker,))
                print(f"Ticker {ticker} eliminato perché non più associato ad altri utenti.")
        
        conn.commit()
        
        conn.close()


        return service_pb2.DeleteUserReply(
            success=True, 
            message=f"Utente {identifier} eliminato con successo!"
        )
    
    def AddTickerUtente(self, request, context):
        """Metodo per aggiungere un ticker all'utente."""
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.AddTickerUtenteReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )
        
        cursor = conn.cursor()

        #controllo se l'utente ha già quel ticker
        cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (identifier, request.ticker))

        if cursor.fetchone() is not None:
            return service_pb2.AddTickerUtenteReply(
                success=False, 
                message=f"Ticker {request.ticker} già presente per l'utente {identifier}!"
            )
                
        cursor.execute("SELECT ticker FROM Tickers WHERE ticker = %s", (request.ticker,))

        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO Tickers (ticker) VALUES (%s)", (request.ticker,))
        
        cursor.execute("INSERT INTO UserTickers (user, ticker, max_value, min_value) VALUES (%s, %s, %s, %s)", (identifier, request.ticker, request.max_value, request.min_value))
        
        conn.commit()
        conn.close()

        return service_pb2.AddTickerUtenteReply(
            success=True, 
            message=f"Ticker {request.ticker} aggiunto all'utente {identifier}!"
        )
    

    def ShowTickersUser(self, request, context):
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.ShowTickersUserReply(
                success=False, 
                message="Errore durante la connessione al database!",
                ticker=""
            )
        
        cursor = conn.cursor()
         #controllo se l'utente ha già quel ticker
        cursor.execute("SELECT ticker, max_value, min_value FROM UserTickers WHERE user = %s", (identifier,))
        ticker= cursor.fetchall()
        
        if not ticker:
            return service_pb2.ShowTickersUserReply(
                success=False, 
                message=f"L'utente {identifier} non ha alcun ticker da visualizzare",
                ticker=""
            )
        
        tickers_list = "\n".join([f"Ticker: {row[0]}, Max: {row[1]}, Min: {row[2]}" for row in ticker])

        
        conn.close()
        return service_pb2.ShowTickersUserReply(
            success=True,
            message="Ticker recuperati con successo",
            ticker=tickers_list
        )
    
    def GetLatestValue(self, request, context):
        """Metodo per ottenere l'ultimo valore dell'azione dell'utente."""
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.GetLatestValueReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )
        
        
        print(f"email utente:  {identifier}")

        cursor = conn.cursor()
        cursor.execute("SELECT Ticker FROM UserTickers WHERE user = %s AND ticker = %s", (identifier,request.ticker))

        row = cursor.fetchone() 

        if row is None:
            print("Nessuna riga trovata per l'utente specificato.")
            return service_pb2.GetLatestValueReply(
            success=False,
            ticker=request.ticker,
            message = "Non hai questo ticker tra quelli di interesse, codice ticker"
            )

        ticker = row[0]

        print(f"ticker: {ticker}")
    
        cursor.execute("SELECT value, timestamp FROM TickerData WHERE ticker = %s ORDER BY timestamp DESC LIMIT 1", (ticker,))

        result = cursor.fetchone()

        if result is None:
            print("Nessuna riga trovata per il ticker specificato.")
            return service_pb2.GetLatestValueReply(
            success=False,
            ticker=ticker,
            message = "Non è stato ancora aggiornato il ticker"
            )

        # Se result non è None, procedi con l'unpacking
        stock_value, timestamp = result

        datetime_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        print(f"stock value: {stock_value}")

        conn.close()

        if stock_value is None:
            print(f"Nessun valore trovato per il ticker {ticker}")
            return service_pb2.GetLatestValueReply(
            success=False,
            ticker=ticker,
            message = "Non abbiamo valori per il ticker"
            )
        
        return service_pb2.GetLatestValueReply(
            success=True, 
            ticker=ticker, 
            stock_value=stock_value, 
            timestamp=datetime_str
        )
    
    def GetAverageValue(self, request, context):
        """Metodo per ottenere la media dei valori dell'azione dell'utente."""
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.GetAverageValueReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )
        
        cursor = conn.cursor()
        cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (identifier,request.ticker))

        row = cursor.fetchone()

        if row is None:
            print("Nessuna riga trovata per l'utente specificato.")
            return service_pb2.GetLatestValueReply(
            success=False,
            ticker=request.ticker,
            message = "Non hai questo ticker tra quelli di interesse, codice ticker"
            )
        
        ticker = row[0]
        
        cursor.execute("SELECT AVG(value), MAX(timestamp) FROM TickerData WHERE ticker = %s ORDER BY timestamp DESC LIMIT %s", (ticker, request.num_values))

        result = cursor.fetchone()

        print(f"valore di ritorno select: {result}")

        if result[0] is None and result[1] is None:
            print("Nessuna riga trovata per il ticker specificato.")
            return service_pb2.GetLatestValueReply(
            success=False,
            ticker=ticker,
            message = "Non è stato ancora aggiornato il ticker"
            )


        media_valori, timestamp = result
        
        conn.close()

        datetime_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

        if media_valori is None:
            return service_pb2.GetAverageValueReply(
            success=False,
            ticker = ticker,
            message = "Non abbiamo valori per il ticker"
        )


        return service_pb2.GetAverageValueReply(
            success=True,
            ticker = ticker,
            average_stock_value=media_valori, 
            timestamp=datetime_str
        )

    #metodo per modificare il valore minimo e massimo di un ticker
    def UpdateMinMaxValue(self, request, context):
        conn = self.get_db_connection()
        if conn is None:
            return service_pb2.UpdateMinMaxValueReply(
                success=False, 
                message="Errore durante la connessione al database!"
            )
        
        cursor = conn.cursor()
        cursor.execute("SELECT ticker FROM UserTickers WHERE user = %s AND ticker = %s", (identifier,request.ticker))

        row = cursor.fetchone()

        if row is None:
            print("Nessuna riga trovata per l'utente specificato.")
            return service_pb2.UpdateMinMaxValueReply(
            success=False,
            ticker=request.ticker,
            message = "Non hai questo ticker tra quelli di interesse, codice ticker"
            )
        
        #prima di modificare controllo se i valori inseriti sono uguali a quelli già presenti
        cursor.execute("SELECT max_value, min_value FROM UserTickers WHERE user = %s AND ticker = %s", (identifier, request.ticker))
        row = cursor.fetchone()
        if row[0] == request.max_value and row[1] == request.min_value:
            return service_pb2.UpdateMinMaxValueReply(
            success=False,
            ticker=request.ticker,
            message = "I valori inseriti sono uguali a quelli già presenti"
            )

        cursor.execute("UPDATE UserTickers SET max_value = %s, min_value = %s WHERE user = %s AND ticker = %s", (request.max_value, request.min_value, identifier, request.ticker))

        conn.commit()
        conn.close()

        return service_pb2.UpdateMinMaxValueReply(
            success=True,
            message="Valori aggiornati con successo"
        )


# Funzione per avviare il server
def serve():
    
    port = '50052'
    
    # Creazione di un server gRPC
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_EchoServiceServicer_to_server(EchoService(), server)

    # Imposta l'indirizzo e la porta dove il server ascolterà
    server.add_insecure_port('[::]:' + port)

    print("Echo Service started, listening on " + port)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
