from .db_connection import get_db_connection


class RegisterUserCommand:
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



class WriteService:
    def __init__(self):
        self.operation = WriteOperation()

    def handle_register_user(self, command: RegisterUserCommand):
        """
        Logica per registrare un utente. Usa il repository per l'accesso al DB.
        """
        self.operation.register_user(command.email, command.ticker, command.max_value, command.min_value)
        print(f"Utente {command.email} registrato con successo con il ticker {command.ticker}!")

