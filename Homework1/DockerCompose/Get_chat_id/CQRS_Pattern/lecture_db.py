from .db_connection import get_db_connection


class ReadService:
    def CheckEmail(self, chat_id):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM Users WHERE chat_id = %s", (chat_id,))
            email = cursor.fetchone()

            return email[0]
        finally:
            conn.close()
            