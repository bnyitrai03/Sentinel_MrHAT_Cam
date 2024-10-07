from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import subprocess
import logging
from datetime import datetime
try:
    from gpiozero import CPUTemperature
except ImportError:
    CPUTemperature = None


class ISystem(ABC):
    @staticmethod
    @abstractmethod
    def get_hardware_info() -> Optional[Dict[str, Any]]:
        pass

    @staticmethod
    @abstractmethod
    def schedule_wakeup(wake_time: Union[str, int, float]) -> None:
        pass


class System(ISystem):
    @staticmethod
    def _get_battery_info() -> Dict[str, Any]:
        battery_result = subprocess.run(
            ['cat', '/sys/class/power_supply/bq2562x-battery/uevent'], stdout=subprocess.PIPE, check=True
        )
        battery_info = battery_result.stdout.decode('utf-8')
        battery_data = dict(line.split("=") for line in battery_info.strip().split("\n"))

        result = subprocess.run(
            ['upower', '-i', '/org/freedesktop/UPower/devices/battery_bq2562x_battery'],
            stdout=subprocess.PIPE,
            check=True,
        )
        info = result.stdout.decode('utf-8')

        for line in info.splitlines():
            if "temperature:" in line:
                battery_data['battery_temperature'] = float(line.split(":")[1].strip().split()[0])

        return battery_data

    @staticmethod
    def _get_charger_info() -> Dict[str, Any]:
        charger_result = subprocess.run(
            ['cat', '/sys/class/power_supply/bq2562x-charger/uevent'], stdout=subprocess.PIPE, check=True
        )
        charger_info = charger_result.stdout.decode('utf-8')

        charger_data = dict(line.split("=") for line in charger_info.strip().split("\n"))

        return charger_data

    @staticmethod
    def _get_cpu_temperature() -> float:
        cpu_temp = CPUTemperature()
        return cpu_temp.temperature

    @staticmethod
    def get_hardware_info() -> Optional[Dict[str, Any]]:
        try:
            battery_data = System._get_battery_info()
            charger_data = System._get_charger_info()
            cpu_temp = System._get_cpu_temperature()

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to gather hardware info: {e}")
            return None

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "cpu_temperature": cpu_temp,
            "battery_temperature": int(battery_data.get("battery_temperature", "0")),
            "battery_percentage": int(battery_data.get("POWER_SUPPLY_CAPACITY", "0")),
            "battery_voltage_now": int(battery_data.get("POWER_SUPPLY_VOLTAGE_NOW", "0")) / 1000000,
            "battery_voltage_avg": int(battery_data.get("POWER_SUPPLY_VOLTAGE_AVG", "0")) / 1000000,
            "battery_current_now": int(battery_data.get("POWER_SUPPLY_CURRENT_NOW", "0")) / 1000000,
            "battery_current_avg": int(battery_data.get("POWER_SUPPLY_CURRENT_AVG", "0")) / 1000000,
            "charger_voltage_now": int(charger_data.get("POWER_SUPPLY_VOLTAGE_NOW", "0")) / 1000000,
            "charger_current_now": int(charger_data.get("POWER_SUPPLY_CURRENT_NOW", "0")) / 1000000,
        }

        return log_data

    @staticmethod
    def schedule_wakeup(wake_time: Union[str, int, float]) -> None:
        """
        Schedule a system wake-up at a specified time.

        Parameters
        ----------
        wake_time : str, int, float
            The time at which the system should wake up.

        Raises
        ------
        subprocess.CalledProcessError
            If the rtcwake command fails to execute.
        """
        try:
            if isinstance(wake_time, str):
                cmd = f"sudo mrhat-rtcwake -d rtc0 -t $(date +%s -d 'today {wake_time}')"
            elif isinstance(wake_time, (int, float)):
                cmd = f"sudo mrhat-rtcwake -d rtc0 -s {str(wake_time)}"
            else:
                raise ValueError("wake_time must be a str, int, or float")

            # Execute the command
            subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set RTC wake-up alarm: {e}")
            logging.error(f"rtcwake error output: {e.stderr}")
            exit(1)
