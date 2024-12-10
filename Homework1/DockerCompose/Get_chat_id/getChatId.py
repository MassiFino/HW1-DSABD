import requests
import mysql.connector
import time
import os

bot_token = os.getenv("BOT_TOKEN")

# Configurazione del database
db_config = {
    'user': 'root',
    'password': '1234',
    'host': 'db',  # Nome del servizio del database in Docker Compose
    'database': 'yfinance_db',
    'port': 3306,
}

def email_exists_for_chat_id(chat_id):
    """Controlla se il chat_id è già associato a un'email nel database."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT email FROM Users WHERE chat_id = %s"
        cursor.execute(query, (chat_id,))
        result = cursor.fetchone()
        return result is not None
    except mysql.connector.Error as err:
        print(f"Errore durante la verifica dell'email: {err}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def send_telegram_message(message, chat_id):
    """Invia un messaggio tramite Telegram a uno specifico chat_id."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"Messaggio inviato con successo a chat_id {chat_id}.")
        else:
            print(f"Errore nell'invio del messaggio a chat_id {chat_id}: {response.json()}")
    except Exception as e:
        print(f"Errore nella connessione con Telegram: {e}")

def save_chat_id_to_db(email, chat_id):
    """Aggiorna il campo chat_id nel database per un'email specifica."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "UPDATE Users SET chat_id = %s WHERE email = %s"
        cursor.execute(query, (chat_id, email))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Chat ID {chat_id} associato con successo all'email {email}.")
        else:
            print(f"Nessun utente trovato con l'email {email}.")
    except mysql.connector.Error as err:
        print(f"Errore durante l'aggiornamento del database: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_updates_and_process():
    """Ascolta continuamente gli aggiornamenti dal bot Telegram."""
    last_update_id = None  # Per tenere traccia dell'ultimo aggiornamento elaborato
    while True:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        if last_update_id:
            url += f"?offset={last_update_id + 1}"  # Prendi solo i nuovi aggiornamenti
        try:
            response = requests.get(url)
            updates = response.json()
            if updates.get("result"):
                for update in updates["result"]:
                    if 'message' in update and 'text' in update['message']:
                        chat_id = update['message']['chat']['id']
                        message = update['message']['text']
                        last_update_id = update['update_id']  # Aggiorna l'ultimo ID elaborato

                        # Controlla se il chat_id è già associato a un'email
                        if not email_exists_for_chat_id(chat_id):
                            send_telegram_message("Per favore, invia la tua email per completare la configurazione.", chat_id)
                        else:
                            print(f"Chat ID {chat_id} già associato a un'email.")

                        # Salva il chat_id se il messaggio contiene un'email valida
                        if "@" in message:
                            save_chat_id_to_db(message.strip(), chat_id)
        except Exception as e:
            print(f"Errore durante il recupero degli aggiornamenti Telegram: {e}")
        
        time.sleep(5)  # Evita di sovraccaricare le richieste all'API Telegram

if __name__ == "__main__":
    print("Avvio del bot Telegram per monitorare aggiornamenti...")
    get_updates_and_process()
