"""
Modulo di logging avanzato con rotazione file per data e dimensione.

Caratteristiche:
- Identificazione del modulo che sta loggando
- File di log con data nel nome
- Rotazione automatica a 10 MB
- Massimo 10 file per giornata
- Formato dettagliato con timestamp, livello, modulo e messaggio
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from pathlib import Path


class CustomRotatingFileHandler(RotatingFileHandler):
    """Handler che cambia il nome del file quando cambia la data."""
    
    def __init__(self, filename_pattern, mode='a', maxBytes=0, backupCount=0, encoding=None):
        self.filename_pattern = filename_pattern
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        filename = filename_pattern.format(date=self.current_date)
        
        # Crea la directory se non esiste
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        
        super().__init__(filename, mode, maxBytes, backupCount, encoding)
    
    def shouldRollover(self, record):
        """Verifica se deve creare un nuovo file (per dimensione o cambio data)."""
        # Controlla se è cambiata la data
        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date != self.current_date:
            self.current_date = current_date
            new_filename = self.filename_pattern.format(date=self.current_date)
            
            # Chiudi il file corrente
            if self.stream:
                self.stream.close()
                self.stream = None
            
            # Aggiorna il baseFilename
            self.baseFilename = os.path.abspath(new_filename)
            
            # Resetta il contatore di backup per la nuova giornata
            self.backupCount = 10
            
            return False
        
        # Controlla la dimensione del file
        return super().shouldRollover(record)


class LoggerManager:
    """Gestisce la configurazione centralizzata del logging."""
    
    _configured = False
    _loggers = {}
    
    @classmethod
    def setup_logging(cls, 
                     log_dir='logs',
                     log_level=logging.DEBUG,
                     max_bytes=10*1024*1024,  # 10 MB
                     backup_count=10,
                     console_output=True):
        """
        Configura il sistema di logging.
        
        Args:
            log_dir: Directory dove salvare i log
            log_level: Livello minimo di logging
            max_bytes: Dimensione massima di ogni file (default 10 MB)
            backup_count: Numero massimo di file per giornata (default 10)
            console_output: Se True, mostra i log anche in console
        """
        if cls._configured:
            return
        
        # Crea la directory dei log
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Pattern del nome file con data
        filename_pattern = os.path.join(log_dir, 'app_{date}.log')
        
        # Formato del log: timestamp | livello | modulo:linea | messaggio
        log_format = '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Crea il formatter
        formatter = logging.Formatter(log_format, date_format)
        
        # Handler per file con rotazione
        file_handler = CustomRotatingFileHandler(
            filename_pattern=filename_pattern,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Configura il logger root
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        
        # Aggiungi handler per console se richiesto
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name=None):
        """
        Ottiene un logger con il nome specificato.
        
        Args:
            name: Nome del logger (opzionale, viene rilevato automaticamente)
        
        Returns:
            Logger configurato
        """
        if not cls._configured:
            cls.setup_logging()
        
        # Se il nome non è specificato, rileva automaticamente il modulo chiamante
        if name is None:
            import inspect
            frame = inspect.currentframe().f_back.f_back
            name = frame.f_globals.get('__name__', 'root')
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]


# Funzione di convenienza per ottenere un logger
def get_logger(name=None):
    """
    Ottiene un logger configurato automaticamente.
    
    Uso:
        from logger import get_logger
        logger = get_logger()  # Rileva automaticamente il modulo
        logger.info("Messaggio di log")
    
    Args:
        name: Nome del logger (opzionale, viene rilevato automaticamente dal modulo chiamante)
    
    Returns:
        Logger configurato
    """
    # Se il nome non è specificato, rileva automaticamente il modulo chiamante
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'root')
    
    return LoggerManager.get_logger(name)


# Esempio di utilizzo
if __name__ == '__main__':
    # Configura il logging (da fare una sola volta all'avvio dell'applicazione)
    LoggerManager.setup_logging(
        log_dir='logs',
        log_level=logging.DEBUG,
        console_output=True
    )
    
    # Ottieni logger per diversi moduli (automaticamente)
    logger_main = get_logger()  # Rileva automaticamente il modulo
    logger_db = get_logger('database')
    logger_api = get_logger('api')
    
    # Esempi di logging
    logger_main.debug("Messaggio di debug dal modulo main")
    logger_main.info("Applicazione avviata")
    logger_db.info("Connessione al database stabilita")
    logger_api.warning("API rate limit vicino al limite")
    logger_db.error("Errore nella query SQL")
    logger_main.critical("Errore critico nell'applicazione")
    
    # Simula molti log per testare la rotazione
    logger_test = get_logger('test')
    for i in range(1000):
        logger_test.info(f"Messaggio di test numero {i} " + "x" * 100)