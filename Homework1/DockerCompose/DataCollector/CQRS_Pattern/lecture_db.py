from .db_connection import get_db_connection


class ReadService:
    def ShowTicker(self):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ticker FROM Tickers")
            tickers = cursor.fetchall()
            if not tickers:
                raise Exception("Nessun ticker presente nel database")
            
            tickers_list = [row[0] for row in tickers]
            return tickers_list
        finally:
            conn.close()
            