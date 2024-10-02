from abc import ABC, abstractmethod
from typing import List


class IRTC(ABC):
    @abstractmethod
    def get_time(self) -> str:
        pass


class RTC(IRTC):
    def _convert_timestamp(self, timestamp) -> str:
        pass

    def _find_line(self, lines: str, target_string) -> str:
        pass

    def _get_timedatectl(self) -> List[str]:
        pass

    def _sync_RTC_to_system(self) -> None:
        pass

    def _sync_system_to_ntp(self, max_retries: int, delay: int) -> bool:
        pass

    def get_time(self) -> str:
        pass
