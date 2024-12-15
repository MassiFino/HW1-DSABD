from .db_connection import get_db_connection


class ReadService:
    def NotifierValues(self):
        conn = get_db_connection()
        if conn is None:
            raise Exception("Errore durante la connessione al database!")
        try:
            cursor = conn.cursor()
            query = """
            SELECT 
                u.email,
                u.chat_id,
                ut.ticker,
                td.value AS latest_value,
                CASE 
                    WHEN ut.min_value > 0 AND td.value < ut.min_value THEN CONCAT('Sotto Min Value: ', ut.min_value)
                    WHEN ut.max_value > 0 AND td.value > ut.max_value THEN CONCAT('Sopra Max Value: ', ut.max_value)
                END AS `condition`
            FROM 
                UserTickers ut
            JOIN 
                TickerData td ON ut.ticker = td.ticker
            JOIN 
                Users u ON ut.user = u.email
            WHERE 
                td.timestamp = (SELECT MAX(timestamp) FROM TickerData WHERE ticker = ut.ticker)
                AND (
                    (ut.min_value > 0 AND td.value < ut.min_value) OR
                    (ut.max_value > 0 AND td.value > ut.max_value)
                );
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        finally:
            conn.close()
            