import struct


switcher = {
    "H": {'len': 1, 'func': lambda v: H2int(v)},
    "f": {'len': 2, 'func': lambda v: f2int(v)},
    "i": {'len': 2, 'func': lambda v: i2int(v)},
    "d": {'len': 4, 'func': lambda v: d2int(v)}
}


def H2int(v):
    return v


def f2int(v):
    return struct.unpack(">HH", struct.pack(">f", v))


def i2int(v):
    return struct.unpack(">HH", struct.pack(">i", v))


def d2int(v):
    return struct.unpack(">HHHH", struct.pack(">d", v))


