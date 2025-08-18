import logging
import os
from typing import cast

from colorlog import ColoredFormatter


class OptionalFieldColoredFormatter(ColoredFormatter):
    def format(self, record: logging.LogRecord) -> str:
        class_attr = getattr(record, "class_name", None)
        record.class_name = f" - {class_attr}" if class_attr else ""
        return cast(str, super().format(record))


class OptionalFieldFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        class_attr = getattr(record, "class_name", None)
        record.class_name = f" - {class_attr}" if class_attr else ""
        return super().format(record)


def setup_logger(
    name: str | None = None,
    level: int = logging.INFO,
    propagate: bool = True,
    consolehandle: bool = False,
    filehandle: bool = False,
    filename: str = "logs/log.txt",
) -> logging.LoggerAdapter:
    """Setup a color logger with the specified name.

    If propagate is ture, it will judge all handlers until the root handlers, \
    and if root handlers already exist, no new handler will be added, even if consolehandle or filehandle is True. \
    If false, it will judge only itself, and it will empty the handlers and create a new one if handlers exists.

    Args:
        name (str or None, optional): The name of logger. If no name is specified, return the root logger. Defaults to None.
        level (int, optional): The logging level of this logger. Defaults to logging.INFO.
        propagate (bool, optional): Whether the log is propagated to the root logger. Defaults to True.
        consolehandle (bool, optional): Add console handler if True. Defaults to False.
        filehandle (bool, optional): Add file handler if True. Defaults to False.
        filename (str, optional): Log file path (used if filehandle is True). Defaults to "logs/log.txt".

    Returns:
        LoggerAdapter: A color logger adapter
    """
    # set logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate
    handle = True

    # prevents duplicate handlers from being added
    if propagate:
        if logger.hasHandlers():
            handle = False
    else:
        if logger.handlers:
            logger.handlers.clear()  # clear old handler

    if handle:
        # set formatter
        formatter = OptionalFieldColoredFormatter(
            "%(log_color)s[%(asctime)s - %(name)s%(class_name)s - %(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red,bg_white",
            },
        )

        formatter_file = OptionalFieldFormatter(
            "%(log_color)s[%(asctime)s - %(name)s%(class_name)s - %(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # adding console handler
        if consolehandle:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        # adding file handler
        if filehandle:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            file_handler = logging.FileHandler(filename)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter_file)
            logger.addHandler(file_handler)

    # creating a LoggerAdapter，adding an additional text field above and below class_name
    logger_adapter = logging.LoggerAdapter(logger, {"class_name": "xxx"})

    return logger_adapter


if __name__ == "__main__":
    pass
