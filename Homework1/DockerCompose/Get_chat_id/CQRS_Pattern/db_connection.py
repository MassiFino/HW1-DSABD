import mysql.connector
import mysql.connector.errors

db_config = {
    'user': 'root',
    'password': '1234',
    'host': 'db',
    'database': 'yfinance_db',
    'port': 3306,
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except mysql.connector.Error as err:
        print(f"Errore durante la connessione al database: {err}")
    return None