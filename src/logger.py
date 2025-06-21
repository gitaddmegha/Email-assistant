import logging

logger = logging.getLogger("EmailAssistant")
logger.setLevel(logging.DEBUG)


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("🔹 [%(levelname)s] %(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(console_handler)
