import logging
import os

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


def get_logger_level():
    log_level_env = os.environ.get("LOGGER_LEVEL")
    try:
        log_level = int(log_level_env)
    except ValueError:
        log_level_str = log_level_env.upper()
        log_level = logging.getLevelName(log_level_str)
        if log_level == 'Level ' + log_level_str:
            raise ValueError(
                'Invalid log level %s. Valid log levels: CRITICAL, ERROR, WARNING, INFO, DEBUG'.format(log_level))
    else:
        if log_level < 1:
            raise ValueError('numeric log levels must be positive, but get %s'.format(log_level))
    return log_level


def get_formatted_logger(log_module_name=None, log_level=None):
    if not log_level:
        log_level = get_logger_level()
    default_logger = logging.getLogger(log_module_name)
    default_logger.setLevel(log_level)
    default_logger.handlers = []
    ch = logging.StreamHandler()
    formatter = CustomJsonFormatter()
    ch.setFormatter(formatter)
    default_logger.addHandler(ch)
    return default_logger
