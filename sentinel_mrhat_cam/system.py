from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union


class ISystem(ABC):
    @abstractmethod
    def get_hardware_info(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def schedule_wakeup(self, wake_time: Union[str, int, float]) -> None:
        pass


class System(ISystem):
    def _get_battery_info(self) -> Dict[str, Any]:
        pass

    def _get_cpu_temperature(self) -> float:
        pass

    def get_hardware_info(self) -> Optional[Dict[str, Any]]:
        pass

    def schedule_wakeup(self, wake_time: Union[str, int, float]) -> None:
        pass
