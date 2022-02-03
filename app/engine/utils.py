import json
import datetime
import logging

def sizeof_fmt(num, suffix='B'):
    """Readable file size
    :param num: Bytes value
    :type num: int
    :param suffix: Unit suffix (optionnal) default = o
    :type suffix: str
    :rtype: str
    """
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def read_json(file_path=""):
    with open(file_path, "r") as f:
        return json.load(f)

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(name)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

class LogManager:

    def __init__(self, name=""):
        self.name = name
        self.logger = logging.getLogger(self.name)

    def log(self, msg=""):
        # print ("{0} | {1} | {2}".format(get_timestamp(), self.name, msg))
        self.logger.info(msg)

    def error(self, msg=""):
        self.logger.error(msg)