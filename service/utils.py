"""
Utils for other modules.
"""

import re
import struct


URL_PATTERN = re.compile(
    r'^(http|https)\://[a-z0-9\-]+(\.[a-z0-9\-]+)+(/.*?)?$'
)


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


def ensure_trailing_slash(path):
    if not path.endswith('/'):
        path += '/'
    return path


def is_valid_url(url):
    return URL_PATTERN.match(url) is not None


def ip_to_int(ip):
    parts = map(int, ip.split('.'))
    return sum(d << (3 - j) * 8 for j, d in enumerate(parts))


def int_to_ip(i):
    parts = ((i >> (3 - j) * 8) % 256 for j in range(4))
    return '.'.join(map(str, parts))


def binary_search(lst, value, func=lambda x: x):
    """
    Searches for the least index of an element in the list 'lst'
    sorted by value (extracted from the element with 'func' or sorted by
    the elements if 'func' is None) such that its value is bigger or equal to
    given 'value'. It returns length of 'lst' if 'value' is bigger than any
    value of the elements. Binary search algorithm is implemented.
    """
    size = len(lst)
    idx = 0
    while size > 0:
        item = lst[idx + size // 2]
        if value > func(item):
            idx += size // 2 + 1
            size = size // 2 + size % 2 - 1
        else:
            size = size // 2
    return idx
