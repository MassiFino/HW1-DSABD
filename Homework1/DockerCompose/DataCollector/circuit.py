# CircuitBreaker

import time
import threading

class CircuitBreaker:
    def __init__(self, failure_threshold=4, recovery_timeout=25, expected_exception=Exception):
        """
        Parameters:
        - failure_threshold (int): Numero di fallimenti consecutivi consentiti prima di aprire il circuito.
        - recovery_timeout (int): Tempo in secondi da attendere prima di tentare di ripristinare il circuito.
        - recovery_timeout (int): Tempo in secondi da attendere prima di tentare di ripristinare il circuito.
        """
        self.failure_threshold = failure_threshold          
        self.recovery_timeout = recovery_timeout           
        self.expected_exception = expected_exception        
        self.failure_count = 0                              
        self.last_failure_time = None                      
        self.state = 'CLOSED'                               
        self.lock = threading.Lock()                        

    def call(self, func, *args, **kwargs):
       
        with self.lock:
            if self.state == 'OPEN':
                # Calcola il tempo trascorso dall'ultimo fallimento
                time_since_failure = time.time() - self.last_failure_time
                if time_since_failure > self.recovery_timeout:
                    # Passa allo stato HALF_OPEN dopo il timeout di recupero
                    self.state = 'HALF_OPEN'
                else:
                    # Il circuito è ancora aperto; rifiuta la chiamata
                    raise CircuitBreakerOpenException("Circuit is open. Call denied.")
            
            try:
                # Tenta di eseguire la funzione
                result = func(*args, **kwargs)
            except self.expected_exception as e:
                # La funzione ha sollevato un'eccezione prevista; incrementa il contatore dei fallimenti
                self.failure_count += 1
                self.last_failure_time = time.time()  # Update the last failure timestamp
                if self.failure_count >= self.failure_threshold:
                    # Raggiunta la soglia di fallimenti; apre il circuito
                    self.state = 'OPEN'
                raise e  
            else:
                
                if self.state == 'HALF_OPEN':
                    # Successo nello stato HALF_OPEN; ripristina il circuito a CLOSED
                    self.state = 'CLOSED'
                    self.failure_count = 0  
                return result  
class CircuitBreakerOpenException(Exception):
    """
    Eccezione sollevata quando il Circuit Breaker è aperto e la richiesta è stata rifiutata.
    """
    def __init__(self, message="Circuit Breaker is OPEN. Operation aborted.", *args):
        # Passa il messaggio e gli eventuali argomenti alla classe base Exception
        super().__init__(message, *args)
        self.message = message  # Memorizza il messaggio di errore
        self.timestamp = time.time()  # Aggiunge un timestamp quando l'eccezione è stata sollevata

    def __str__(self):
        """
        Restituisce una stringa descrittiva dell'eccezione.
        """
        return f"[{self.timestamp}] {self.message}"

    def get_timestamp(self):
        """
        Restituisce il timestamp quando l'eccezione è stata sollevata.
        """
        return self.timestamp

