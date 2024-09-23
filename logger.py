import logging


class Logger:
    @staticmethod
    def setup_logger(logger_name: str):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Create a console handler and set the level to info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handler
        formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - {logger_name} - %(message)s')
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        if not logger.hasHandlers():
            logger.addHandler(console_handler)

        return logger
