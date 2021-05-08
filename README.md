# Logitech G203 Prodigy / G203 LightSync Mouse LED control

Allows you to control the LED lighting of your G203 Prodigy or G203 LightSync Mouse programmatically. \
Inspired by and based on [g810-led](https://github.com/MatMoul/g810-led).

## Requirements

- Python 3.5+
- PyUSB 1.0.2+
- **Root privileges**

## Installation

1) Clone the repository: `git clone https://github.com/smasty/g203-led.git`
2) Prepare _virtualenv_: `virtualenv ./env`
3) Install dependencies: `env/bin/pip install -r requirements.txt`
4) Run (as root): `sudo ./g203-led.py solid 00FFFF`

## Usage

```
Usage:
    g203-led [lightsync] solid {color} - Solid color mode
    g203-led [lightsync] cycle [{rate} [{brightness}]] - Cycle through all colors
    g203-led [lightsync] breathe {color} [{rate} [{brightness}]] - Single color breathing
    g203-led [lightsync] intro {on|off} - Enable/disable startup effect
    g203-led [lightsync] dpi {dpi} - Set mouse dpi

Arguments:
    Color: RRGGBB (RGB hex value)
    Rate: 100-60000 (Number of milliseconds. Default: 10000ms)
    Brightness: 0-100 (Percentage. Default: 100%)
    DPI: 200-8000 (Prodigy), 50-8000 (Lightsync)

Additional features for G203 LightSync:
    g203-led lightsync triple {color color color} - Sets all 3 colors from left to right.
    g203-led lightsync wave {rate} [{brightness} [{direction}]] - Like cycle but appears to move right or left.
    g203-led lightsync blend [{rate} [{brightness}]] - Like breathe with the side colors changing after some delay.
    
    Direction is either "left" or "right". Default: right).

Note that the lightsync setting will not persist.
There is onboard memory for persistence but it is not used by this script.
```
