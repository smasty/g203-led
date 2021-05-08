#!env/bin/python

# Logitech G203 Prodigy / G203 LightSync Mouse LED control
# https://github.com/smasty/g203-led
# Authors: Smasty, TheAquaSheep (LightSync support)
# Licensed under the MIT license.

import sys
import usb.core
import usb.util
import re
import binascii

g203_vendor_id =  0x046d
g203_prodigy_product_id = 0xc084
g203_lightsync_product_id = 0xc092
g203_product_id = g203_prodigy_product_id

default_rate = 10000
default_brightness = 100
default_direction = 'right'


dev = None
wIndex = None


def help():
    print("""Logitech G203 Prodigy / Lightsync Mouse LED control

Usage:
\tg203-led [lightsync] solid {color} - Solid color mode
\tg203-led [lightsync] cycle [{rate} [{brightness}]] - Cycle through all colors
\tg203-led [lightsync] breathe {color} [{rate} [{brightness}]] - Single color breathing
\tg203-led [lightsync] intro {on|off} - Enable/disable startup effect
\tg203-led [lightsync] dpi {dpi} - Set mouse dpi

Arguments:
\tColor: RRGGBB (RGB hex value)
\tRate: 1000-60000 (Number of milliseconds. Default: 10000ms)
\tBrightness: 1-100 (Percentage. Default: 100%)
\tDPI: 200-8000 (Prodigy), 50-8000 (Lightsync)

Assumes Prodigy by default unless "lightsync" is given as the first command argument.
This ensures backward compatibility.
Lightsync additional features:
\tg203-led lightsync triple {color color color} - Sets all 3 colors from left to right.
\tg203-led lightsync wave {rate} [{brightness} [{direction}]] - Like cycle but appears to move right or left.
\tg203-led lightsync blend [{rate} [{brightness}]] - Like breathe with the side colors changing after some delay.

\tDirection is either "left" or "right". Default: right).

Note that the lightsync setting will not persist.
There is onboard memory for persistence but it is not used by this script.""")



def main():
    if(len(sys.argv) < 2):
        help()
        sys.exit()

    args = sys.argv + [None] * (6 - len(sys.argv))

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
    elif mode == 'dpi':
        set_dpi(process_dpi(args[2]))
    elif mode == 'lightsync':
        global g203_product_id
        g203_product_id = g203_lightsync_product_id
        mode = args[2]
        if mode == 'solid':
            set_ls_solid(process_color(args[3]))
        elif mode == 'cycle':
            set_ls_cycle(process_rate(args[3]), process_brightness(args[4]))
        elif mode == 'breathe':
            set_ls_breathe(
                process_color(args[3]),
                process_rate(args[4]),
                process_brightness(args[5])
            )
        elif mode == 'intro':
            set_ls_intro(args[3])
        elif mode == 'dpi':
            set_dpi(process_dpi(args[3]))
        elif mode == 'triple':
            set_ls_triple(
                process_color(args[3]),
                process_color(args[4]),
                process_color(args[5])
            )
        elif mode == 'wave':
            set_ls_wave(
                process_rate(args[3]),
                process_brightness(args[4]),
                process_direction(args[5])
            )
        elif mode == 'blend':
            set_ls_blend(process_rate(args[3]), process_brightness(args[4]))
        else:
            print_error('Unknown lightsync mode.')
    else:
        print_error('Unknown mode.')


def print_error(msg):
    print('Error: ' + msg)
    sys.exit(1)


def process_color(color):
    if not color:
        print_error('No color specified.')
    if color[0] == '#':
        color = color[1:]
    if not re.match('^[0-9a-fA-F]{6}$', color):
        print_error('Invalid color specified.')
    return color.lower()

def process_rate(rate):
    if not rate:
        rate = default_rate
    try:
        return '{:04x}'.format(max(1000, min(65535, int(rate))))
    except ValueError:
        print_error('Invalid rate specified.')

def process_brightness(brightness):
    if not brightness:
        brightness = default_brightness
    try:
        return '{:02x}'.format(max(1, min(100, int(brightness))))
    except ValueError:
        print_error('Invalid brightness specified.')

def process_direction(direction):
    if not direction:
        direction = default_direction
    else:
        if not (direction == 'left' or direction == 'right'):
            print_error('Invalid direction specified.')
    return direction

def process_dpi(dpi):
    if not dpi:
        print_error('No DPI specified.')
    lower_lim = 200
    if g203_product_id == g203_lightsync_product_id:
        lower_lim = 50
    try:
        return '{:04x}'.format(max(lower_lim, min(8000, int(dpi))))
    except ValueError:
        print_error('Invalid DPI specified.')
    return dpi


def set_led_solid(color):
    return set_led('01', color + '0000000000')

def set_led_breathe(color, rate, brightness):
    return set_led('03', color + rate + '00' + brightness + '00')

def set_led_cycle(rate, brightness):
    return set_led('02', '0000000000' + rate + brightness)


def set_led(mode, data):
    global dev
    global wIndex

    prefix = '11ff0e3b00'
    suffix = '000000000000'
    send_command(prefix + mode + data + suffix)


def set_intro_effect(arg):
    if arg == 'on' or arg == '1':
        toggle = '01'
    elif arg == 'off' or arg == '0':
        toggle = '02'
    else:
        print_error('Invalid value.')

    send_command('11ff0e5b0001'+toggle+'00000000000000000000000000')

def set_dpi(dpi):
    cmd = '10ff0a3b00{}'.format(dpi)
    send_command(cmd, disable_ls_onboard_memory=False)

def set_ls_solid(color):
    cmd = '11ff0e1b0001{}0000000000000001000000'.format(color)
    send_command(cmd, disable_ls_onboard_memory=True)

def set_ls_cycle(rate, brightness):
    cmd = '11ff0e1b00020000000000{}{}000001000000'.format(rate, brightness)
    send_command(cmd, disable_ls_onboard_memory=True)

def set_ls_breathe(color, rate, brightness):
    cmd = '11ff0e1b0004{}{}00{}00000001000000'.format(color, rate, brightness)
    send_command(cmd, disable_ls_onboard_memory=True)

def set_ls_intro(arg):
    if arg == 'on' or arg == '1':
        toggle = '01'
    elif arg == 'off' or arg == '0':
        toggle = '02'
    else:
        print_error('Invalid value.')
    cmd = '11ff0e3b010001{}000000000000000000000000'.format(toggle)
    send_command(cmd, disable_ls_onboard_memory=False)

def set_ls_triple(color_left, color_middle, color_right):
    cmd = '11ff121b01{}02{}03{}00000000'.format(color_left, color_middle, color_right)
    send_command(cmd, disable_ls_onboard_memory=False)

def set_ls_wave(rate, brightness, direction):
    rate_U8 = rate[0:2]
    rate_L8 = rate[2:4]
    state = '01'
    if direction == 'left':
        state = '06'
    cmd = '11ff0e1b0003000000000000{}{}{}{}01000000'.format(rate_L8, state, brightness, rate_U8)
    send_command(cmd, disable_ls_onboard_memory=True)

def set_ls_blend(rate, brightness):
    rate_U8 = rate[0:2]
    rate_L8 = rate[2:4]
    cmd = '11ff0e1b0006000000000000{}{}{}0001000000'.format(rate_L8, rate_U8, brightness)
    send_command(cmd, disable_ls_onboard_memory=True)

def clear_ls_buffer(): #tested on lightsync but may also affect prodigy
    try:
        while True:
            dev.read(0x82, 20)
    except usb.core.USBError:
        return

def send_command(data, disable_ls_onboard_memory=False, clear_ls_buf=False):
    attach_mouse()

    if clear_ls_buf: # if this is ever needed in practise the default can be changed above.
        clear_ls_buffer()

    if disable_ls_onboard_memory:
        dev.ctrl_transfer(0x21, 0x09, 0x210, wIndex, binascii.unhexlify('10ff0e5b010305'))
        dev.read(0x82, 20)

    wValue=0x211
    if len(data) == 14:
        wValue = 0x210

    dev.ctrl_transfer(0x21, 0x09, wValue, wIndex, binascii.unhexlify(data))
    dev.read(0x82, 20)

    if data[0:8] == '11ff121b':
        apply_triple_cmd = '11ff127b00000000000000000000000000000000'
        dev.ctrl_transfer(0x21, 0x09, 0x211, wIndex, binascii.unhexlify(apply_triple_cmd))
        dev.read(0x82, 20)

    if clear_ls_buf: # done again to ensure the buffer did not fill between the last clear and cmd
        clear_ls_buffer()

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
