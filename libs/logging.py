import logging
import os.path


def configure_logging(working_dir: str) -> logging.Logger:
    """
    Configures a logger for the application that writes log messages to both a file and the console.

    The method sets up a logger named 'buildanddeploy' with DEBUG level for detailed logging.
    A file handler is created to store logs in a specified working directory with detailed logs,
    and a stream handler is used for console output to display informative messages.

    :param working_dir: The directory where the log file will be created.
    :type working_dir: str

    :return: The configured logger instance.
    :rtype: logging.Logger
    """
    # Create a logger
    logger = logging.getLogger("buildanddeploy")
    logger.setLevel(logging.DEBUG)

    # Create a formatter to define the log format
    formatter_file = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    formatter_console = logging.Formatter("%(levelname)s - %(message)s")

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler(os.path.join(working_dir, "build.log"), mode="w")
    file_handler.setFormatter(formatter_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter_file)

    # Create a stream handler to print logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter_console)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
