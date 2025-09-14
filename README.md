# Whisplay Lumon MDR UI

An UI project build for mini Lumon MDR machine, build on Raspberry Pi zero 2w, PiSugar3 and Whisplay Hat.

![whisplay_lumon_mdr_ui](https://github.com/PiSugar/whisplay-lumon-mdr-ui/blob/main/mdr_demo.gif?raw=true)

## How To Use

* Install Whisplay Driver, please refer to https://github.com/PiSugar/whisplay
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
* (Optional) Add to autostart
```
sudo bash startup.sh
```
