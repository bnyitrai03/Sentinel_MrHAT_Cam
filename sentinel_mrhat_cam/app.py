from .states import Context


class App:
    def __init__(self):
        self._context: Context = Context()

    def run(self) -> None:
        while True:
            self._context.request()
