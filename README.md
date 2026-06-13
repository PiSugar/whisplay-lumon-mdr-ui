# Whisplay Lumon MDR UI

An UI project build for mini Lumon MDR machine, build on Raspberry Pi zero 2w, PiSugar3 and Whisplay Hat.

![whisplay_lumon_mdr_ui](https://github.com/PiSugar/whisplay-lumon-mdr-ui/blob/main/mdr_demo.gif?raw=true)

## How To Use

* Install the Whisplay sound card driver. The UI auto-detects the unified `whisplaysound` card and remains compatible with legacy Whisplay card names.
* Download or clone this repo
```shell
git clone https://github.com/PiSugar/whisplay-lumon-mdr-ui.git
```
* Install python dependencies
```shell
pip install -r requirements.txt --break-system-packages
```
* Start UI
```shell
python lumon-ui.py
```
If `whisplay-daemon` is running, the UI registers as the `whisplay-lumon-mdr-ui` app and uses daemon-managed display, button, backlight, and LED access. If the daemon is not available, it falls back to direct hardware access.
* (Optional) Add to autostart
```
sudo bash startup.sh
```

## 3D Print Enclosure
https://github.com/PiSugar/suit-cases/tree/main/pisugar3-whisplay-lumon-mdr
