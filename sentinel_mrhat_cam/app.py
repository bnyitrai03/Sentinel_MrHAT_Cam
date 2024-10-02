from .states import Context
import time


class App:
    def __init__(self):
        self._context = Context()
        print("Context created")

    def run(self) -> None:
        while True:
            self._context.request()
            time.sleep(10)
            print("Slept 10 sec")
