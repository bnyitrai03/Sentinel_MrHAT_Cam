import logging
import time
import unittest
from unittest import TestCase

from sentinel_mrhat_cam import log_execution_time


class UtilsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig()

    def setUp(self):
        print()

    def test_log_exec_time_with_operation(self):

        @log_execution_time("test")
        def test_func():
            time.sleep(0.1)

        test_func()

    def test_log_exec_time_without_operation(self):

        @log_execution_time()
        def test_func():
            time.sleep(0.1)

        test_func()


if __name__ == "__main__":
    unittest.main()
