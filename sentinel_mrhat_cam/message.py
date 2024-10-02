class MessageCreator:
    def __init__(self, system: ISystem, rtc: IRTC, camera: ICamera):
        self._camera = camera
        self._rtc = rtc
        self._system = system

    def create_message(self) -> str:
        pass

    def log_hardware_info(self) -> None:
        pass