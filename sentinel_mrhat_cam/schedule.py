class Schedule:
    def __init__(self):
        self._time_offset: int = 0

    def adjust_time(self, timestamp: str) -> str:
        pass

    def calculate_shutdown_duration(self, waiting_time: float) -> float:
        pass

    def get_wake_time(self, shutdown_duration: float) -> datetime:
        pass

    def should_shutdown(self, waiting_time: float) -> bool:
        pass

    def shutdown(self, waiting_time: float, current_time: datetime) -> None:
        pass

    def working_time_check(self, wake_up_timestamp: str, shut_down_timestamp: str) -> None:
        pass