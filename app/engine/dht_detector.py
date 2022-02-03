import random
import time
import datetime

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


    def get_data(self):
        return self._dict_data

    # get data from DHT sensor
    def get_dht_data(self):
        try:
            hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, self._pin)
            if hum is not None and temp is not None:
                return round(temp, 1), round(hum, 1)
        except Exception as err:
            return random.randrange(40, 60), random.randrange(-10, 40)


    def run(self):

        while True:
            temp, hum  = self.get_dht_data()

            self._dict_data = {
                "dateTimeTake": f"{datetime.datetime.now()}".split(".")[0],
                "temperature": temp,
                "humidity": hum,
            }

            time.sleep(2)