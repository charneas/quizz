import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Crée le dossier logs s'il n'existe pas
logs_dir = "logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure le logger principal
logger = logging.getLogger("quiz_app")
logger.setLevel(logging.DEBUG)

# Handler pour fichier avec rotation
file_handler = RotatingFileHandler(
    os.path.join(logs_dir, "quiz_app.log"),
    maxBytes=1024 * 1024,  # 1 MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Handler pour console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Format des logs
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Ajoute les handlers au logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Fonction utilitaire pour logger les erreurs avec le traceback
def log_error(error: Exception, context: str = None):
    """Log une erreur avec son traceback et le contexte"""
    import traceback
    error_details = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": type(error).__name__,
        "message": str(error),
        "context": context,
        "traceback": traceback.format_exc()
    }
    
    logger.error(
        f"Error in {context if context else 'unknown context'}\n"
        f"Type: {error_details['type']}\n"
        f"Message: {error_details['message']}\n"
        f"Traceback:\n{error_details['traceback']}"
    )
