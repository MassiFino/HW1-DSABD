import grpc
import service_pb2, service_pb2_grpc
import uuid
from email_validator import validate_email, EmailNotValidError
import csv



def genera_userid():
    return str(uuid.uuid4())

def genera_requestid():
    return str(uuid.uuid4())

def verifica_email(email):
    try:
        # Validazione dell'email
        valid = validate_email(email)
        # Restituisce l'email normalizzata se valida
        return valid.email
    except EmailNotValidError as e:
        # Errore se l'email non è valida
        print(str(e))
        return None
    
    # Caricamento ticker
def carica_ticker(filepath):
    try:
        with open(filepath, mode='r') as file:
            reader = csv.DictReader(file)
            tickers = {row['Symbol'] for row in reader}
        return tickers
    except FileNotFoundError:
        print("File dei ticker non trovato.")
        return set()
    
def verifica_ticker(ticker):
    # Percorso file ticker
    filepath = './nasdaq-listed-symbols.csv'
    valid_tickers = carica_ticker(filepath)
    if not ticker or ticker.strip() == "":
        print("Ticker non valido. Il ticker non può essere vuoto o composto solo da spazi. Riprova.")
        return False
    if ticker.upper() in valid_tickers:
        return True
    print("Ticker non valido. Riprova.")
    
    return False

def inserisci_valori_min_max():
    max_value = None
    min_value = None

    while True:
        valori = input("Vuoi inserire un valore di minimo o massimo (o entrambi) da tener traccia per il tuo ticker? (s/n): ").lower()
        if valori in ('s', 'n'):
            if valori == 's':
                # Inserimento valore massimo
                while True:
                    max_input = input("Inserisci il valore massimo (oppure 0 se non vuoi inserirlo): ").strip()
                    if max_input == '0':
                        max_value = None
                        break
                    else:
                        try:
                            max_value = float(max_input)
                            break
                        except ValueError:
                            print("Devi inserire un valore numerico (float). Riprova.")
                
                # Inserimento valore minimo
                while True:
                    min_input = input("Inserisci il valore minimo (oppure 0 se non vuoi inserirlo): ").strip()
                    if min_input == '0':
                        min_value = None
                        break
                    else:
                        try:
                            min_value = float(min_input)
                            # Verifica coerenza solo se entrambi sono impostati
                            if max_value is not None and min_value >= max_value:
                                print("Il valore minimo deve essere inferiore al valore massimo. Riprova.")
                            else:
                                break
                        except ValueError:
                            print("Devi inserire un valore numerico (float). Riprova.")

                # Se l'utente non inserisce uno dei due valori, restituisce 0 al suo posto
                return (max_value if max_value is not None else 0, 
                        min_value if min_value is not None else 0)

            else:
                # Utente ha scelto 'n', quindi nessun valore
                return 0, 0
        else:
            print("Scelta non valida. Riprova.")




def reg_login(stub):
    
    while True:
            print("\nScegli un'opzione:")
            print("1. Registra utente")
            print("2. Login utente")
            print("3. Esci")

            scelta = input("inserisci l'operazione che vuoi effettuare: ")

            if scelta == '1':
                while True:
                    email = input("Inserisci email: ")

                    if verifica_email(email):
                        break
                    print("Devi inserire una email valida")

                while True:
                    ticker = input("Inserisci ticker iniziale: ").upper()
                    if verifica_ticker(ticker):
                        break
                #chiedo all'utente se vuole inserire un valore massimo e minimo
                max_value, min_value = inserisci_valori_min_max()
                       
                userid = genera_userid()

                # Crea i metadati da passare nelle richieste gRPC
                metadata = [
                    ('userid', userid)
                ]

                request = service_pb2.RegisterUserRequest(email=email, ticker=ticker, max_value=max_value, min_value=min_value)
                try:
                    response = stub.RegisterUser(request, metadata=metadata)
                    if not response.success:
                        print(f"Risultato: {response.message}")
                    else:
                        print(f"Risultato: {response.message}")
                        operazioni(stub)
        
                except grpc.RpcError as e:
                    print(f"Errore: {e.code()} - {e.details()}")
                

            elif scelta == '2':
                while True:
                    email = input("Inserisci email: ")

                    if verifica_email(email):
                        break

                    print("Devi inserire una email valida")

                request = service_pb2.LoginUserRequest(email=email)
                try:
                    response = stub.LoginUser(request)

                    if not response.success:
                        print(f"Risultato: {response.message}")

                    else:
                        print(f"Risultato: {response.message}")
                        operazioni(stub)

                except grpc.RpcError as e:
                    print(f"Errore: {e.code()} - {e.details()}")

            elif scelta == "3":
                print("Uscita...")
                break

            else:
                print("Scelta non valida. Riprova.")




def operazioni(stub):

    while True:
        print("\nScegli un'opzione:")
        print("1. Aggiungi ticker")
        print("2. Visualizza tutti i ticker") 
        print("3. Sostituisci ticker")
        print("4. Elimina un ticker ")
        print("5. Modifica/Aggiungi valore minimo e massimo di un ticker") 
        print("6. Ottieni ultimo valore")
        print("7. Ottieni media valori")
        print("8. Elimina utente")
        print("9. Esci")

        scelta = input("Inserisci il numero dell'operazione: ")

        if scelta == "1":
            while True:
                ticker = input("Inserisci ticker: ").upper()
                if verifica_ticker(ticker):  # Controllo del ticker
                    break

            max_value, min_value = inserisci_valori_min_max()
            
            request = service_pb2.AddTickerUtenteRequest(ticker=ticker, max_value=max_value, min_value=min_value)

            try:
                response = stub.AddTickerUtente(request)
                print(f"Risultato: {response.message}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")

        elif scelta == "2":
            request = service_pb2.ShowTickersUserRequest()
            try:
                response = stub.ShowTickersUser(request)
                if not response.success:
                    print(f"{response.message}")
                else:
                    print(f"Ticker associati all'utente:\n {response.ticker}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")
      

        elif scelta == "3":
            while True:
                while True:
                    #facciamo selezionare all'utente il ticker che vuole inserire
                    ticker_old = input("Inserisci ticker da sostituire: ").upper()
                    if verifica_ticker(ticker_old):  # Controllo del ticker
                        break
                while True:
                    ticker = input("Inserisci nuovo ticker: ").upper()
                    if verifica_ticker(ticker):  # Controllo del ticker
                        break
                
                if ticker != ticker_old:
                    break
                print("Il nuovo ticker deve essere diverso da quello vecchio. Riprova.")

            max_value, min_value = inserisci_valori_min_max()


            requestid = genera_requestid()

            # Crea i metadati da passare nelle richieste gRPC
            metadata = [
                ('requestid', requestid)
            ]
            
            request = service_pb2.UpdateUserRequest(ticker_old=ticker_old, ticker=ticker, max_value=max_value, min_value=min_value)
            try:
                response = stub.UpdateUser(request, metadata=metadata)
                print(f"Risultato: {response.message}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")

                
        elif scelta == "4":
            while True:
                #facciamo selezionare all'utente il ticker che vuole inserire
                ticker= input("Inserisci ticker da eliminare: ").upper()
                if verifica_ticker(ticker):  # Controllo del ticker
                    break
            request = service_pb2.DeleteTickerUserRequest(ticker=ticker)
            try:
                response = stub.DeleteTickerUser(request)
                print(f"Risultato: {response.message}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")
        elif scelta == "5":
            while True:
                ticker = input("Inserisci ticker di cui vuoi aggiungere/ modificare il valore: ").upper()
                if verifica_ticker(ticker):  # Controllo del ticker
                    break

            max_value, min_value = inserisci_valori_min_max()

            request = service_pb2.UpdateMinMaxValueRequest(ticker=ticker, max_value=max_value, min_value=min_value)
            try:
                response = stub.UpdateMinMaxValue(request)
                if not response.success:
                    print(f"{response.message}: {response.ticker}")
                else:
                    print(f"{response.message}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")



        elif scelta == "6":
            while True:
                ticker = input("Inserisci ticker: ").upper()
                if verifica_ticker(ticker):  # Controllo del ticker
                    break
        
            request = service_pb2.GetLatestValueRequest(ticker=ticker)
            try:
                response = stub.GetLatestValue(request)
                if not response.success:
                    print(f"{response.message}: {response.ticker}")
                else:
                    print(f"Ticker: {response.ticker}, Valore: {response.stock_value}, Timestamp: {response.timestamp}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")

        elif scelta == "7":
            while True:
                ticker = input("Inserisci ticker: ").upper()
                if verifica_ticker(ticker):  # Controllo del ticker
                    break

            while True:
                user_input = input("Numero di valori da considerare: ")

                # Verifica se l'input è un numero intero
                if user_input.isdigit():
                    num_values = int(user_input)
            
                    # Controlla che il numero sia maggiore di 0
                    if num_values > 0:
                        break  # Esce dal ciclo se il numero è valido
                    else:
                        print("Il numero di valori deve essere maggiore di 0. Riprova.")
                else:
                    print("Devi inserire un numero intero valido. Riprova.")

            request = service_pb2.GetAverageValueRequest(ticker=ticker, num_values=num_values)
            try:
                response = stub.GetAverageValue(request)
                if not response.success:
                    print(f"{response.message}: {response.ticker}")
                else:
                    print(f"Ticker: {response.ticker},Media: {response.average_stock_value}, Timestamp: {response.timestamp}")
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")

        elif scelta == "8":
            request = service_pb2.DeleteUserRequest()
            try:
                response = stub.DeleteUser(request)
                print(f"Risultato: {response.message}")
                break
            except grpc.RpcError as e:
                print(f"Errore: {e.code()} - {e.details()}")

        elif scelta == "9":
            print("Uscita...")
            break

        else:
            print("Scelta non valida. Riprova.")

def main():
    # Genera i metadati una sola volta

    with grpc.insecure_channel('localhost:50052') as channel:
        stub = service_pb2_grpc.EchoServiceStub(channel)
        reg_login(stub)

if __name__ == "__main__":
    main()
