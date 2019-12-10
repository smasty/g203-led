#!env/bin/python

#
# Logitech Mouse LED control
#
#  * G403 Prodigy Mouse
#  * G403 HERO Gaming Mouse
#
# https://github.com/stelcheck/g403-led
# Author: Smasty, hello@smasty.net
# Licensed under the MIT license.

import sys
import usb.core
import usb.util
import re
import binascii

vendor_id =  0x046d # Logitech

compatible_devices = {
    0xc083: "G403 Legacy Mouse",
    0xc08f: "G403 HERO Gaming Mouse",
}

default_rate = 10000
default_brightness = 100

dev = None
wIndex = None


def help():
    print("""Logitech G403 Mouse LED control

Usage:
\tg403-led solid {color} - Solid color mode
\tg403-led cycle [{rate} [{brightness}]] - Cycle through all colors
\tg403-led breathe {color} [{rate} [{brightness}]] - Single color breathing
\tg403-led intro {on|off} - Enable/disable startup effect

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
    elif mode == 'intro':
        set_intro_effect(args[2])
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
    global device
    global wIndex

    prefix_scrollwheel = '11ff0e3b00'
    prefix_logo = '11ff0e3b01'

    suffix = '000000000000'
    send_command(prefix_scrollwheel + mode + data + suffix)
    send_command(prefix_logo + mode + data + suffix)


def set_intro_effect(arg):
    if arg == 'on' or arg == '1':
        toggle = '01'
    elif arg == 'off' or arg == '0':
        toggle = '02'
    else:
        print_error('Invalid value.')

    send_command('11ff0e5b0001'+toggle+'00000000000000000000000000')


def send_command(data):
    attach_mouse()
    device.ctrl_transfer(0x21, 0x09, 0x0211, wIndex, binascii.unhexlify(data))
    detach_mouse()


def attach_mouse():
    global device
    global wIndex

    for product_id, product_title in compatible_devices.items():
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if device is not None:
            #print("Found {}".format(product_title))
            break

    if device is None:
        print_error('No compatible devices found.')

    wIndex = 0x01
    if device.is_kernel_driver_active(wIndex) is True:
        device.detach_kernel_driver(wIndex)
        usb.util.claim_interface(device, wIndex)


def detach_mouse():
    global device
    global wIndex
    if wIndex is not None:
        usb.util.release_interface(device, wIndex)
        device.attach_kernel_driver(wIndex)
        device = None
        wIndex = None


if __name__ == '__main__':
    main()
