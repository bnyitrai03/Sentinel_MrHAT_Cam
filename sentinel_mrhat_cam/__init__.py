"""
<br>
Welcome to the documentation. 🐦

[Project Homepage](https://github.com/Aitia-IIOT/sentinel-mrhat-cam)

[![website](https://github.com/leventenyiri/AitiA/actions/workflows/documentation-release.yml/badge.svg)](https://github.com/leventenyiri/AitiA/actions/workflows/documentation-release.yml)

[![Python release](https://github.com/Aitia-IIOT/sentinel-mrhat-cam/actions/workflows/python-release.yml/badge.svg)](https://github.com/Aitia-IIOT/sentinel-mrhat-cam/actions/workflows/python-release.yml)

[![Python test](https://github.com/leventenyiri/AitiA/actions/workflows/python-test.yml/badge.svg)](https://github.com/leventenyiri/AitiA/actions/workflows/python-test.yml)

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fleventenyiri%2FAitiA%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

<br><br>

## Overview

The device consists of a Raspberry Pi Zero 2W,  MrHat by [Effective-Range™](https://effective-range.com), a camera📸, a battery🔋 and a solar panel☀️.
Its function is taking pictures periodically and sending them through MQTT. The period, mode and working time is configurable by sending a config file to the device.

#### Period
How often the images will be taken.

#### Mode
Either **one-shot** (take one picture, send it, then shut down), **always-on** (taking and sending them as fast as it can without break), and **periodic** (taking and sending pictures with a given period).
In production only the **periodic** mode will be used.

About where to send the config, see the [Messaging](https://leventenyiri.github.io/AitiA/sentinel_mrhat_cam.html#messaging) section.

The end product will come in a water and dust-proof case with wifi antenna and IP68 rated button, currently the prototype is in an electrical box, originally rated IP68, but a hole had to be drilled for the USB cable, so using duct tape around the area is recommended if you plan on using it in the rain.

![Hole in case](https://github.com/bnyitrai03/rpizero_storage/blob/main/HoleInBox.jpg?raw=true)

<br><br><br><br>

## Raspbian Image installation 🛠️

The device comes with the OS installed on the SD card already, but if there is an update or bug fix, [this guide](https://github.com/EffectiveRange/raspbian-image-repository?tab=readme-ov-file#install-your-custom-images-to-an-sd-card) should be followed to upgrade the OS to the new image.
The image installation guide is made by [Effective-Range™](https://effective-range.com).

<br><br><br><br>

## Power management ⚡

Currently, if you want to charge the battery you have to first fully disconnect the power (no USB cable, no battery connected), and then first connect the battery and then plug in the USB cable. The order matters here!

Alternatively, you can shut down the device with the following command:
```bash
sudo shutdown -h now
```
The green LED on the Raspberry (not the **MrHAT**!) will blink 10 times (can take a bit of time for it to start blinking), it will shut down after. Once it has fully shut down **pressing the button** will wake it up, and if the USB cable and the battery are both connected it will be charging.

![Button](https://github.com/bnyitrai03/rpizero_storage/blob/main/Button.jpg?raw=true)

In case of the button malfunctioning, simply pull out and plug in the USB cable.

#### Meaning of LED-s
The green LED on the Raspberry shows whether its on or off.

![PiLED](https://github.com/bnyitrai03/rpizero_storage/blob/main/PiLED.jpg?raw=true)


On the **MrHAT** there are 3 LED-s. If one blue LED is on, then it means its running off of the battery.
![1LED](https://github.com/bnyitrai03/rpizero_storage/blob/main/1LED.jpg?raw=true)

If two blue LED-s are on, it means that it receives power through the USB-C port.

![2LED](https://github.com/bnyitrai03/rpizero_storage/blob/main/2LED.jpg?raw=true)

The green LED on the **MrHAT** is also on, if the battery is being charged.

![3LED](https://github.com/bnyitrai03/rpizero_storage/blob/main/3LED.jpg?raw=true)

<br><br><br><br>


## Login 🔐

First configure which network the Pi connects to. The [Effective-Range™](https://effective-range.com) **WifiManager** lets you do just that!

When you power on the device, if it cannot connect to any network, it will become an available network that you can connect to.
Connect to it, then it will take you to a page, where you can input the SSID and password of the network that you want the Pi to connect to.
Here you can [learn more](https://github.com/EffectiveRange/wifi-manager) about the **WifiManager**.

To communicate with the device via **ssh**, make sure you are connected to the **same network** as the Pi!

Alternatively, you can also configure the network manually if you prefer.
```bash
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```
Example:
```bash
network={
        ssid="TMIT_C1_2_4"
        psk="example_password"
        disabled=0
        priority=0
}
network={
        ssid="OnePlus"
        psk="dogdogdog"
        disabled=0
        priority=1
}
```

Here, a higher number means higher priority, so in this example, if both OnePlus and TMIT_C1_2_4 are available, it will connect to OnePlus.

What the **WifiManager** does, is that every time you configure a network through it, it writes it into this file with a higher priority than the last one.

#### Example of ssh using ip address:
Connect the device to the PC using the USB-C port on the **MrHAT** and use a program like PuTTY to communicate through serial port. Check the device manager to see which COM port the device uses. Inside PuTTY it should look like this:

![Image of PuTTY](https://github.com/bnyitrai03/rpizero_storage/blob/main/PuTTY.png?raw=true)

(On windows for the serial line just write COM...)

Baud rate: 115200

Click on Open, click inside the window and press Enter. After a while it will ask for the username and the password, during testing:

Username: admin

Password: admin

![Image of login](https://github.com/bnyitrai03/rpizero_storage/blob/main/PuTTY_Login.png?raw=true)

Write hostname -I, and you will get the ip address.

![Hostname](https://github.com/bnyitrai03/rpizero_storage/blob/main/PuTTY_Hostname.png?raw=true)

You can now log in using this ip address like so:

```bash
ssh admin@192.168.0.103
```

#### Example of ssh using mDNS:

Once you have successfully connected to the device you will know its name, you can also use this to log in, you just have to put .local after the name.
```bash
ssh admin@er-edge-16b9ac84.local
```

#### Example of ssh using [key based login](https://github.com/EffectiveRange/devc-effectiverange/wiki/Configuring-SSH-targets):
In the linked tutorial the name the Host myhost, you can name it however you like.
```bash
ssh myhost
```

<br><br><br><br>

## Running the script 🚀
Before running the script make sure that the Pi can synchronize with an NTP server, or you have to set the correct datetime manually!
```bash
sudo date -s "2024-08-14 15:57:40"
```

By default the script is running automatically as soon as the device has booted up. This is thanks to a daemon, which is starting a bash script on boot. The bash script starts the python script, handles additional logging, and restarts the script or the device based on exit codes from the python script.

If you dont want the script to start on boot, then you have to disable the daemon responsible for that.

```bash
sudo systemctl disable sentinel-mrhat-cam.service

sudo reboot
```

To make it start on boot:

```bash
sudo systemctl enable sentinel-mrhat-cam.service

sudo reboot
```

You can also start the script manually.

Make sure you are in the home/admin folder.
```bash
cd
```
Then run the bash script.
```bash
bash sentinel_mrhat_cam.sh
```

As its running itt will create a bash_log.txt and a hardware_log.txt file in the home/admin folder on the Pi. The bash_log contains information about whats happening within the script and the hardware_log, as the name suggests lets us know about specifics of the hardware, like CPU temperature and battery voltage...

If for some reason you want to run the python script straight up, you can do that too.
```bash
python3 -m sentinel_mrhat_cam.main
```

Be aware, that this way you will miss out on the bash_log and the hardware_log, it will also not handle the cases where the script exits with an exit code.

<br><br><br><br>

## Messaging 💬

You can edit the ip address of the broker, the port and the QoS level in the [static_config.py](https://leventenyiri.github.io/AitiA/sentinel_mrhat_cam/static_config.html) file. The names of the mqtt topics can also be found here, along with other constants.

Each device will have a unique name and topic for receiving the config. E.g: for one device the topic where the config is sent may look like this: **settings/er-edge-16b9ac84**, for another it may look like this: **settings/er-edge-1169bc8a**. In the examples below we will simply use **er-edge** as the username.

**Subscribe topic:** `config/er-edge`

The defaul sentinel_app_config.json message:

```json
{
     "quality": "3K",
     "mode": "periodic",
     "period": 15,
     "wakeUpTime": "06:59:31",
     "shutDownTime": "22:00:00"
}
```

- In case there is something wrong with the received config, the default will be used.
- If the `period` in the config is smaller than the `SHUTDOWN_THRESHOLD` in the [static_config.py](https://leventenyiri.github.io/AitiA/sentinel_mrhat_cam/static_config.html) file, then the device will never shut down, it will just wait inside the script when necessary. If its bigger, it will shut down for the appropriate amount of time between taking and sending pictures.

**Publish topic:** `er-edge/confirm`

`config-ok` OR `config-nok|{error desc}`

- Once a `sentinel_app_config.json` file is sent to the device, a message will be sent back to this topic.
- If everything was fine, it will send a `config-ok` message.
- If something went wrong it will send a `config-nok` followed by the description of the problem.

**Publish topic:** `mqtt/rpi/image`

Example message:

```json
{
     "timestamp":"2024-07-11T18:52:05.179690+00:00",
     "image":"/9j/4AAQSkZJRgABAQAAAQAB...."
     "cpuTemp":35.6,
     "batteryTemp":48.5,
     "batteryCharge": 95
}
```

- Along with the image we also send a timestamp (ISO8601), and a few hardware values.

**Publish topic:** `er-edge/logging`

Example log messages:
```bash
2024-08-12 16:27:55 - root - INFO - Image capture time: (capture) took 0.118763 seconds
2024-08-12 16:27:55 - root - INFO - Battery temp: 23.4°C, battery percentage: 90 %, CPU temp: 54.768°C
2024-08-12 16:27:56 - root - INFO - Creating the json message (create_message) took 0.386625 seconds
2024-08-12 16:27:56 - root - INFO - Taking a picture and sending it (transmit_message) took 0.734755 seconds
2024-08-12 16:27:56 - root - INFO - Sleeping for 9.0 seconds
```

- Logs will be sent to this topic.
- The level of the log messages we want to send can be set using the `LOG_LEVEL` variable in [static_config.py](https://leventenyiri.github.io/AitiA/sentinel_mrhat_cam/static_config.html). Currently it is set to `DEBUG`.

<br><br><br><br>

## Scheduling ⏱️

To accurately send the pictures with the given period, we have to measure the runtime of the script, and take it into account. We also need to know how much time it takes to shut down and boot up.

To do this, we need the date of the last time the device has shut down, so that after waking up we can calculate how much time has passed. We have to write these values into a file, to make them persist between shutdown cycles. We call this file `state_file.json`, here is an example of it:
```json
{
    "boot_shutdown_time": 15.0,
    "last_shutdown_time": "2024-08-06T09:26:48+00:00"
}
```
The next time the device wakes up, it will read the values from this file, it will use the `last_shutdown_time`, along with the `period` from the config and the runtime of the script to decide how long it has to be shut down. It will also update the `last_shutdown_time` when it shuts down, so it can be used in the next iteration.

<br><br><br><br>

## Gathering data 📊

While the device is running, its collecting data about the hardware. This data is logged into the `hardware_log.txt` file in the home/admin directory on the Pi.

If you want to visualize this data, use this [matlab script](https://github.com/leventenyiri/Hardware_data_visualizer).

Currently, because of a faulty driver, you have to measure the consumption and the charging data separately, because when its charging (even if its charging with 1mA and the device is consuming 400mA), the battery current will just show 0mA (when in reality it should show -399mA).

If you measure the data while the device does not receive any power through the USB-C port however, you will get an accurate reading. Just keep in mind that if you are measuring data about charging, the consumption data will probably be off by quite a bit.

<br><br><br><br>

## Hardware 📟

![Prototype Schematic](https://github.com/bnyitrai03/rpizero_storage/blob/main/Protot%C3%ADpus%20rajz%20V1.3.png?raw=true)

![DeviceWithSolarPanel](https://github.com/bnyitrai03/rpizero_storage/blob/main/DeviceWithSolarPanel.jpg?raw=true)

![StandaloneDevice](https://github.com/bnyitrai03/rpizero_storage/blob/main/StandaloneDevice.jpg?raw=true)

### Components

- **Single-Board Computer**: [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)

- **Raspbery extension Hat**: [MrHAT](https://effective-range.com/hardware/mrhat/)

- **Camera module**: [Arducam IMX519 PDAF&CDAF Autofocus Camera Module](https://www.arducam.com/product/imx519-autofocus-camera-module-for-raspberry-pi-arducam-b0371/)

- **Solar Panel**: [Reolink Solar Panel 2](https://www.bestmarkt.hu/reolink-rlsolpbb2-kulteri-okos-kamera-usb-napelem-p853135)

- **SD card**: [SanDisk microSDHC Ultra 32GB](https://www.alza.hu/sandisk-microsdhc-ultra-32gb-sd-adapter-d6250713.htm?kampan=arukereso_hu_prislusenstvi-pro-it-tv_pametove-karty_microsdhc/xc_dt807j2f2b1b&utm_source=arukereso_hu&utm_medium=product&utm_campaign=arukereso_hu_prislusenstvi-pro-it-tv_pametove-karty_microsdhc/xc_dt807j2f2b1b&aku=324206e06a9b4d5089a463dab6911ac6)
"""

from .static_config import *
from .logger import *
from .camera import *
from .rtc import *
from .system import *
from .states import *
from .mqtt import *
from .schedule import *
from .app_config import *
from .message import *
