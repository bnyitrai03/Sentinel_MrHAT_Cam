from typing import List, Dict, Any


class Config:
    def __init__(self):
        self._list: List = []
        self._path: str = ""
        self.active: Dict = {}
        self.uuid: str = ""

    def check_for_new_config(self) -> None:
        pass

    def get_default_config(self) -> Dict[str, Any]:
        pass

    def load(self) -> None:
        pass

    def validate_config(self, new_config) -> None:
        pass

    def validate_period(self, period) -> None:
        pass

    def validate_time_format(self, new_config) -> None:
        pass
