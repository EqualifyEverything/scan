import logging

# Add logging to each file with
#   from utils.watch import logger


# Set up logger: "A11yLogger"
logger = logging.getLogger("A11y🪵 ")

# Check if logger already has handlers
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)

    # Create console handler and set level to info
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
    ch.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(ch)

def configure_logger():
     # Use the logger from logging_config.py
     global logger
     logger = logging.getLogger("A11y🪵 ")