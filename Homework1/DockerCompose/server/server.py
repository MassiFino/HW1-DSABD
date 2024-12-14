import grpc
from concurrent import futures
import service_pb2, service_pb2_grpc
import mysql.connector
import mysql.connector.errors
from threading import Lock
from datetime import datetime
import CQRS_Pattern.command_db as command_db
import CQRS_Pattern.lecture_db as lecture_db

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
    #Read
    def LoginUser(self, request, context):
        "Login Utente"
        read_service=lecture_db.ReadService()
        try:
            global identifier
            identifier= request.email
            read_service.login_user(request.email)
            
            response=service_pb2.LoginUserReply(
                success=True, 
                message=f"Ti stiamo reindirizzando alla pagina principale"
            )
            return response
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response = service_pb2.LoginUserReply(
                success=False,
                message=str(e)
            )   
        
        return response


    #Write
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
    #Write
    def UpdateUser(self, request, context):
        """Metodo per aggiornare il codice dell'azione dell'utente."""

        meta = dict(context.invocation_metadata())

        requestid = meta.get('requestid', 'unknown')

        print(f"Richiesta di aggionamento con RquestID: {requestid}")

        with cache_lock:
            if requestid in cache["update_cache"]:
                print(f"Risposta in cache per RequestID {requestid}")
                return cache["update_cache"][requestid]

        cmd = command_db.UpdateUserCommand(
            email=identifier,
            ticker_old=request.ticker_old,
            ticker=request.ticker,
            max_value=request.max_value,
            min_value=request.min_value
        )
        
        write_service = command_db.WriteService()
        try:
            write_service.handle_update_user(cmd)
        
        
            response = service_pb2.UpdateUserReply(
            success=True, 
            message=f"Codice dell'azione aggiornato per l'utente {identifier}!"
            )
            with cache_lock:
                cache["update_cache"][requestid] = response
        
            return response
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response = service_pb2.UpdateUserReply(
                success=False,
                message=str(e)
            )
            with cache_lock:
                cache["update_cache"][requestid] = response
        
            return response
        
    #Write
    def DeleteTickerUser(self, request,context):
       
        cmd = command_db.DeleteTickerUserCommand(
            email=identifier,
            ticker=request.ticker,
           
        )
        write_service = command_db.WriteService()
        try:
            # Tenta di eseguire la logica di scrittura
            write_service.handle_delete_ticker_user(cmd)
           
            response = service_pb2.DeleteTickerUserReply(
                success=True, 
                message=f"Ticker {request.ticker} dell'utente : {identifier} eliminato con successo!"
            )
            return response

        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response = service_pb2.DeleteTickerUserReply(
                success=False,
                message=str(e)
            )
            return response
    #Write
    def DeleteUser(self,request,context):
        """Metodo per eliminare un utente."""
        cmd = command_db.DeleteUserCommand(
            email=identifier
           
        )
        write_service = command_db.WriteService()
       
        try:
            write_service.handle_delete_user(cmd)
            response = service_pb2.DeleteUserReply(
            success=True, 
            message=f"Utente {identifier} eliminato con successo!"
            )
            return response
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response = service_pb2.DeleteTickerUserReply(
                success=False,
                message=str(e)
            )
            return response
    #Write 
    def AddTickerUtente(self, request, context):
        cmd = command_db.AddTickerCommand(
            email=identifier,
            ticker=request.ticker,
            max_value=request.max_value,
            min_value=request.min_value
           
        )
        write_service = command_db.WriteService()
        try:
            # Tenta di eseguire la logica di scrittura
            write_service.handle_addTicker(cmd)

            response = service_pb2.AddTickerUtenteReply(
                success=True, 
                message=f"Ticker {request.ticker} aggiunto all'utente {identifier}!"
        )
            return response
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response = service_pb2.AddTickerUtenteReply(
                success=False,
                message=str(e)
            )
            return response
    #Read
    def ShowTickersUser(self, request, context):
        read_service=lecture_db.ReadService()
        try:
            tickers_list=read_service.show_ticker_user(identifier)
            response= service_pb2.ShowTickersUserReply(
                success=True,
                message="Ticker recuperati con successo",
                ticker=tickers_list
            )
            return response 
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response= service_pb2.ShowTickersUserReply(
                success=False,
                message=str(e),
                ticker=""
            )
        return response
        
       
        
    #Read
    def GetLatestValue(self, request, context):
        read_service=lecture_db.ReadService()
        try:
            stock_value, datetime_str =read_service.get_latest_value(identifier,request.ticker)
            response=service_pb2.GetLatestValueReply(
                success=True, 
                ticker=request.ticker, 
                stock_value=stock_value,
                timestamp=datetime_str
            )
            return response 
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response=service_pb2.GetLatestValueReply(
                success=False,
                ticker="",
                stock_value="",
                timestamp="",
                message=str(e)
            )
        return response
    #Read
    def GetAverageValue(self, request, context):
        read_service=lecture_db.ReadService()
        try:
            average_stock_value,datetime_str =read_service.get_average_value(identifier,request.ticker,request.num_values)
            response= service_pb2.GetAverageValueReply(
                success=True,
                ticker = request.ticker,
                average_stock_value=average_stock_value, 
                timestamp=datetime_str
            )
            return response 
        except Exception as e:
        # Se c'è stata un'eccezione, significa che c'è un problema di connessione
        # o l'utente esiste già nel DB, o altre cause.
            response=service_pb2.GetAverageValueReply(
                success=False, 
                ticker=request.ticker,
                message=str(e),
                average_stock_value="", 
                timestamp=""
            )
        return response
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
