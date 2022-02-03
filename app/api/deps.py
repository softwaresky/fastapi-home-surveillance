import threading
import time


def func(n=10):

    for i in  range(n):
        print (i)
        time.sleep(1)


t = threading.Thread(target=func, args=(100,))

print (t.daemon)
t.start()