# Logitech G203 Prodigy Mouse LED control

Allows you to control the LED lighting of your G203 Prodigy Mouse programmatically.
Inspired by and based on [g810-led](https://github.com/MatMoul/g810-led).

It does not work as-is with the new G203 Lightsync Mouse.

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
    g203-led solid {color} - Solid color mode
    g203-led cycle [{rate} [{brightness}]] - Cycle through all colors
    g203-led breathe {color} [{rate} [{brightness}]] - Single color breathing
    g203-led intro {on|off} - Enable/disable startup effect

Arguments:
    Color: RRGGBB (RGB hex value)
    Rate: 100-60000 (Number of milliseconds. Default: 10000ms)
    Brightness: 0-100 (Percentage. Default: 100%)
```
