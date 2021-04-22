#!/usr/bin/python
import sys
import string
import fcntl
import errno
from ctypes import (
        Structure,
        c_int,
        c_uint,
        c_short,
        c_ushort,
        )


# To run without root permissions, add this udev rule:
#
#   ACTION=="add", SUBSYSTEM=="usbmisc", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="c084", SYMLINK+="logitech_g203", GROUP="adm"
#
# (Or change GROUP="adm" to MODE="0666" to make available to all users.)
# Ideally, would also check ATTRS{bInterfaceNumber}=="01",
# but all ATTRS must match on the same device,
# and the interface doesn't have idVendor or idProduct.


# Translated from asm-generic/ioctl.h

_IOC_NRBITS   = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS  = 2

_IOC_NRSHIFT   = 0
_IOC_TYPESHIFT = (_IOC_NRSHIFT+_IOC_NRBITS)
_IOC_SIZESHIFT = (_IOC_TYPESHIFT+_IOC_TYPEBITS)
_IOC_DIRSHIFT  = (_IOC_SIZESHIFT+_IOC_SIZEBITS)

_IOC_NONE  = 0
_IOC_WRITE = 1
_IOC_READ  = 2

def _IOC(dir,type,nr,size):
    if isinstance(type, str):
        type = ord(type)
    return (((dir)  << _IOC_DIRSHIFT) |
            ((type) << _IOC_TYPESHIFT) |
            ((nr)   << _IOC_NRSHIFT) |
            ((size) << _IOC_SIZESHIFT))

def _IOC_TYPECHECK(t): return t

def _IO(type,nr):        return _IOC(_IOC_NONE,(type),(nr),0)
def _IOR(type,nr,size):  return _IOC(_IOC_READ,(type),(nr),(_IOC_TYPECHECK(size)))
def _IOW(type,nr,size):  return _IOC(_IOC_WRITE,(type),(nr),(_IOC_TYPECHECK(size)))
def _IOWR(type,nr,size): return _IOC(_IOC_READ|_IOC_WRITE,(type),(nr),(_IOC_TYPECHECK(size)))


# Translated from linux/input.h

BUS_USB = 0x03


# Translated from linux/hiddev.h

class hiddev_devinfo(Structure):
    _fields_ = [
        ("bustype", c_uint),
        ("busnum", c_uint),
        ("devnum", c_uint),
        ("ifnum", c_uint),
        ("vendor", c_short),
        ("product", c_short),
        ("version", c_short),
        ("num_applications", c_uint),
    ]

class hiddev_report_info(Structure):
    _fields_ = [
        ("report_type", c_uint),
        ("report_id", c_uint),
        ("num_fields", c_uint),
    ]

HID_REPORT_ID_UNKNOWN = 0xffffffff
HID_REPORT_ID_FIRST   = 0x00000100
HID_REPORT_ID_NEXT    = 0x00000200
HID_REPORT_ID_MASK    = 0x000000ff
HID_REPORT_ID_MAX     = 0x000000ff

HID_REPORT_TYPE_INPUT   = 1
HID_REPORT_TYPE_OUTPUT  = 2
HID_REPORT_TYPE_FEATURE = 3
HID_REPORT_TYPE_MIN     = 1
HID_REPORT_TYPE_MAX     = 3

class hiddev_field_info(Structure):
    _fields_ = [
        ("report_type", c_uint),
        ("report_id", c_uint),
        ("field_index", c_uint),
        ("maxusage", c_uint),
        ("flags", c_uint),
        ("physical", c_uint),
        ("logical", c_uint),
        ("application", c_uint),
        ("logical_minimum", c_int),
        ("logical_maximum", c_int),
        ("physical_minimum", c_int),
        ("physical_maximum", c_int),
        ("unit_exponent", c_uint),
        ("unit", c_uint),
    ]

class hiddev_usage_ref(Structure):
    _fields_ = [
        ("report_type", c_uint),
        ("report_id", c_uint),
        ("field_index", c_uint),
        ("usage_index", c_uint),
        ("usage_code", c_uint),
        ("value", c_int),
    ]

HID_MAX_MULTI_USAGES = 1024
class hiddev_usage_ref_multi(Structure):
    _fields_ = [
        ("uref", hiddev_usage_ref),
        ("num_values", c_uint),
        ("values", c_int * HID_MAX_MULTI_USAGES),
    ]

HID_VERSION = 0x010004

HIDIOCGVERSION    = _IOR('H', 0x01, len(bytes(c_int())))
HIDIOCGDEVINFO    = _IOR('H', 0x03, len(bytes(hiddev_devinfo())))
HIDIOCSREPORT     = _IOW('H', 0x08, len(bytes(hiddev_report_info())))
HIDIOCGREPORTINFO = _IOWR('H', 0x09, len(bytes(hiddev_report_info())))
HIDIOCGFIELDINFO  = _IOWR('H', 0x0A, len(bytes(hiddev_field_info())))
HIDIOCSUSAGES     = _IOW('H', 0x14, len(bytes(hiddev_usage_ref_multi())))


# Values based on hardware observation

G203_VENDOR_ID =  0x046d
G203_PRODUCT_ID = 0xc084
G203_LED_APPLICATION = 0xff000002


# Application code follows

def get_report_and_field(fd, report_type, application):
    """The report and field for a particular application

    Returns (report_info, field_info, field_index)
    """
    found = None
    next_id = HID_REPORT_ID_FIRST
    while True:
        ri = hiddev_report_info()
        ri.report_type = report_type
        ri.report_id = next_id
        try:
            fcntl.ioctl(fd, HIDIOCGREPORTINFO, ri)
        except IOError as exn:
            if exn.errno != errno.EINVAL:
                raise
            # No more reports
            break

        for field in range(ri.num_fields):
            fi = hiddev_field_info()
            fi.report_type = ri.report_type
            fi.report_id = ri.report_id
            fi.field_index = field
            fcntl.ioctl(fd, HIDIOCGFIELDINFO, fi)
            if fi.application == application:
                if found is not None:
                    raise Exception("Duplicate")
                found = (ri, fi, field)
            next_id = HID_REPORT_ID_NEXT | ri.report_id

    if not found:
        raise Exception("Not found")
    return found


def main(argv):
    # usage: g203-led-usbhid.py /dev/logitech_g203 332200
    _, fname, color = argv

    if len(color) != 6 or not (set(color) <= set(string.hexdigits)):
        raise Exception("Bad color")
    vals = bytes.fromhex("ff0e3b0001" + color + "0000000000000000000000")

    with open(fname, "r") as fd:
        # Check hiddev driver version.
        version = c_int()
        fcntl.ioctl(fd, HIDIOCGVERSION, version)
        if version.value != HID_VERSION:
            raise Exception("Wrong version")

        # Check device information against expected values.
        devinfo = hiddev_devinfo()
        fcntl.ioctl(fd, HIDIOCGDEVINFO, devinfo)
        if devinfo.bustype != BUS_USB:
            raise Exception("Not USB")
        if devinfo.ifnum != 1:
            raise Exception("Not interface 1")
        if c_ushort(devinfo.vendor).value != G203_VENDOR_ID:
            raise Exception("Wrong vendor")
        if c_ushort(devinfo.product).value != G203_PRODUCT_ID:
            raise Exception("Wrong product")

        # Find the report and field.
        ori, ofi, field_index = get_report_and_field(
                fd, HID_REPORT_TYPE_OUTPUT, G203_LED_APPLICATION)
        # Check field length.  Driver subtracts 1.
        if ofi.field_index + 1 != len(vals):
            raise Exception("Wrong length")

        # Set the full buffer of usages, then send the report.
        uref = hiddev_usage_ref()
        uref.report_type = HID_REPORT_TYPE_OUTPUT
        uref.report_id = ori.report_id
        uref.field_index = field_index
        uref.usage_index = 0
        multi = hiddev_usage_ref_multi()
        multi.uref = uref
        multi.num_values = len(vals)
        multi.values[:len(vals)] = vals
        fcntl.ioctl(fd, HIDIOCSUSAGES, multi)
        fcntl.ioctl(fd, HIDIOCSREPORT, ori)


if __name__=="__main__":
    sys.exit(main(sys.argv))
