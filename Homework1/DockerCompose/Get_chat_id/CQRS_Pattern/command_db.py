from .db_connection import get_db_connection

#Ogni operazione di scrittura deve avere un oggetto comando dedicato che rappresenta i dati necessari per l'esecuzione
class SaveChatIdCommand:
    def __init__(self, email, chat_id):
        self.email = email
        self.chat_id = chat_id
        
class WriteOperation:
    def SaveChatId(self,email, chat_id):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("UPDATE Users SET chat_id = %s WHERE email = %s", (chat_id, email))
            conn.commit()
            if cursor.rowcount > 0:
                raise Exception(f"Chat ID {chat_id} associato con successo all'email {email}.")
            else:
                raise Exception(f"Nessun utente trovato con l'email {email}.")

        finally:
            conn.close()

            
             
class WriteService:
    def __init__(self):
        self.operation = WriteOperation()

    def handle_save_chatId(self, command: SaveChatIdCommand):
        self.operation.SaveChatId(command.email, command.chat_id)
        print(f"Chat ID {command.chat_id} salvato con successo!")
        
            
        
   
