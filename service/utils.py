"""
Utils for other modules.
"""

import struct


def ip_to_bytes(ip):
    return bytes(map(int, ip.split('.')))


def str_to_bytes(s, limit):
    b = s.encode()
    assert len(b) <= limit
    b += b'\x00' * (limit - len(b))
    return b


def float_to_bytes(z):
    return struct.pack('d', z)


def ip_from_bytes(b):
    return '.'.join(map(str, b))


def str_from_bytes(b):
    b = b.split(b'\x00', 1)[0]
    return b.decode()


def float_from_bytes(b):
    return struct.unpack('d', b)[0]
