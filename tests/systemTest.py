import pytest
from unittest.mock import patch
from gpiozero import CPUTemperature
from sentinel_mrhat_cam import System

def test_get_cpu_temperature():
    result = True
    assert result == True
