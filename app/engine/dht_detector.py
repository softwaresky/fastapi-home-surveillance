import random
import time
import datetime
from app.engine import utils

try:
    import Adafruit_DHT
except:
    pass

from app.engine.base_class import ThreadBase


class DhtDetector(ThreadBase):

    def __init__(self, dht_pin=4):
        super(self.__class__, self).__init__()
        self.name = self.__class__.__name__
        self._dict_data = {"temperature": 0.0,
                          "humidity": 0.0}
        self._pin = dht_pin
        self.log_manager = utils.LogManager(self.name)


    def get_data(self):
        return self._dict_data

    # get data from DHT sensor
    def get_dht_data(self):
        try:
            hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, self._pin)
            if hum is not None and temp is not None:
                temp = round(temp, 1)
                hum = round(hum, 1)
            return temp, hum
        except Exception as err:
            return random.randrange(40, 60), random.randrange(-10, 40)


    def run(self):

        self.log_manager.log("Start measurement ...")

        self.is_running = True

        while self.is_running:
            temp, hum  = self.get_dht_data()

            self._dict_data = {
                "dateTimeTake": f"{datetime.datetime.now()}".split(".")[0],
                "temperature": temp,
                "humidity": hum,
            }

            time.sleep(2)

        self.is_running = False