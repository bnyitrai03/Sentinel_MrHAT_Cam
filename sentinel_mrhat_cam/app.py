class App:
    def __init__(self, camera: ICamera, communication: ICommunication, rtc: IRTC, system: ISystem):
        self._context: Context = Context()

    def start(self) -> None:
        self._context.set_state(InitState())

    def run(self) -> None:
        while True:
            self._context.request()
