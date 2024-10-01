# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/bnyitrai03/Sentinel_MrHAT_Cam/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                   |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| sentinel\_mrhat\_cam/\_\_init\_\_.py   |       10 |        0 |        0 |        0 |    100% |           |
| sentinel\_mrhat\_cam/app.py            |       58 |       37 |        8 |        2 |     35% |55-60, 63->62, 68-69, 72->71, 76, 82-83, 112-133, 139-141, 153-154, 169-173 |
| sentinel\_mrhat\_cam/app\_config.py    |       68 |       51 |       34 |        4 |     21% |40-55, 80-96, 99->98, 108-115, 118->117, 141-158, 161->160, 178-183, 186->185, 201-205 |
| sentinel\_mrhat\_cam/camera.py         |       41 |       26 |        8 |        1 |     33% |6, 51-68, 82-86, 89->88, 98-103 |
| sentinel\_mrhat\_cam/logger.py         |       64 |       47 |       14 |        0 |     22% |53-58, 72-83, 92-97, 106-110, 130-137, 163-174, 183-188 |
| sentinel\_mrhat\_cam/mqtt.py           |       92 |       71 |       14 |        0 |     20% |9-11, 54-61, 64, 67, 80-107, 121-150, 186-192, 224-231, 263-267, 275-277 |
| sentinel\_mrhat\_cam/schedule.py       |       49 |       35 |        6 |        0 |     25% |11-12, 28, 44-52, 68-69, 85-92, 96-98, 114-136 |
| sentinel\_mrhat\_cam/static\_config.py |       27 |        5 |        0 |        0 |     81% |12, 34, 43, 49, 54 |
| sentinel\_mrhat\_cam/system.py         |      131 |       95 |       52 |       12 |     26% |33->32, 34-35, 38->37, 39-40, 44->43, 58-78, 81->80, 90-91, 94->93, 134-155, 158->157, 215-252, 265->264, 283-287, 290->289, 322-333, 336->335, 372-385, 388->387, 411-414, 417->416, 448-449, 452->451, 475-505 |
| sentinel\_mrhat\_cam/transmit.py       |       84 |       58 |       16 |        2 |     28% |51-54, 67-76, 112-120, 123->122, 153-179, 185-186, 200-203, 206->205, 231-243, 257-268 |
| sentinel\_mrhat\_cam/utils.py          |       20 |        0 |        4 |        1 |     96% |    12->11 |
| tests/utilsTest.py                     |       21 |        0 |        6 |        3 |     89% |12->11, 21->20, 29->28 |
|                              **TOTAL** |  **665** |  **425** |  **162** |   **25** | **32%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/bnyitrai03/Sentinel_MrHAT_Cam/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/bnyitrai03/Sentinel_MrHAT_Cam/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/bnyitrai03/Sentinel_MrHAT_Cam/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/bnyitrai03/Sentinel_MrHAT_Cam/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fbnyitrai03%2FSentinel_MrHAT_Cam%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/bnyitrai03/Sentinel_MrHAT_Cam/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.