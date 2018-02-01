#!env/bin/python

# Logitech G203 Prodigy Mouse LED control
# https://github.com/smasty/g203-led
# Author: Smasty, hello@smasty.net
# Licensed under the MIT license.

import sys
import usb.core
import usb.util
import re
import binascii

g203_vendor_id =  0x046d
g203_product_id = 0xc084

default_rate = 10000
default_brightness = 100


dev = None
wIndex = None


def help():
    print("""Logitech G203 Prodigy Mouse LED control

Usage:
\tg203-led solid {color} - Solid color mode
\tg203-led cycle [{rate} [{brightness}]] - Cycle through all colors
\tg203-led breathe {color} [{rate} [{brightness}]] - Single color breathing

Arguments:
\tColor: RRGGBB (RGB hex value)
\tRate: 100-60000 (Number of milliseconds. Default: 10000ms)
\tBrightness: 0-100 (Percentage. Default: 100%)""")


def main():
    if(len(sys.argv) < 2):
        help()
        sys.exit()

    args = sys.argv + [None] * (5 - len(sys.argv))

    mode = args[1]
    if mode == 'solid':
        set_led_solid(process_color(args[2]))
    elif mode == 'cycle':
        set_led_cycle(process_rate(args[2]), process_brightness(args[3]))
    elif mode == 'breathe':
        set_led_breathe(
            process_color(args[2]),
            process_rate(args[3]),
            process_brightness(args[4])
        )
    else:
        print_error('Unknown mode.')


def print_error(msg):
    print('Error: ' + msg)
    sys.exit(1)


def process_color(color):
    if not color:
        print_error('No color specifed.')
    if color[0] == '#':
        color = color[1:]
    if not re.match('^[0-9a-fA-F]{6}$', color):
        print_error('Invalid color specified.')
    return color.lower()

def process_rate(rate):
    if not rate:
        rate = default_rate
    try:
        return '{:04x}'.format(max(100, min(65535, int(rate))))
    except ValueError:
        print_error('Invalid rate specified.')

def process_brightness(brightness):
    if not brightness:
        brightness = default_brightness
    try:
        return '{:02x}'.format(max(1, min(100, int(brightness))))
    except ValueError:
        print_error('Invalid brightness specified.')


def set_led_solid(color):
    return set_led('01', color + '0000000000')

def set_led_breathe(color, rate, brightness):
    return set_led('03', color + rate + '00' + brightness + '00')

def set_led_cycle(rate, brightness):
    print(rate, brightness)
    return set_led('02', '0000000000' + rate + brightness)


def set_led(mode, data):
    global dev
    global wIndex

    prefix = '11ff0e3b00'
    suffix = '000000000000'
    data = prefix + mode + data + suffix

    attach_mouse()
    dev.ctrl_transfer(0x21, 0x09, 0x0211, wIndex, binascii.unhexlify(data))
    detach_mouse()


def attach_mouse():
    global dev
    global wIndex
    dev = usb.core.find(idVendor=g203_vendor_id, idProduct=g203_product_id)
    if dev is None:
        print_error('Device {:04x}:{:04x} not found.'.format(g203_vendor_id, g203_product_id))
    wIndex = 0x01
    if dev.is_kernel_driver_active(wIndex) is True:
        dev.detach_kernel_driver(wIndex)
        usb.util.claim_interface(dev, wIndex)


def detach_mouse():
    global dev
    global wIndex
    if wIndex is not None:
        usb.util.release_interface(dev, wIndex)
        dev.attach_kernel_driver(wIndex)
        dev = None
        wIndex = None


if __name__ == '__main__':
    main()
