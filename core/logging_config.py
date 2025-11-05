import logging
import sys


def setup_logging():
    """Sets up a basic logger to print formatted logs to the console."""
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger()

    # Clear any existing handlers to avoid duplicate logs
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Set up a handler to print to the console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Set the logging level to INFO
    root_logger.setLevel(logging.INFO)

    logging.info("Logging configured successfully.")
