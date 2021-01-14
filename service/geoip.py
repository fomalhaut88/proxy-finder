"""
GeoipDB is a singleton (with the method get_instance) that implements
geo information about IP.

Before the use it is necessary to prepare binary database. To do it:

    1. Set environment variable GEOIP_DB_PATH with the desired path to the
        database.
    2. Download geo data as CSV from
        https://db-ip.com/db/download/ip-to-city-lite.
        The direct link is similar to
        https://download.db-ip.com/free/dbip-city-lite-2020-12.csv.gz.
    3. Extract CSV from from the archive.
    4. Run prepare_geoip_db with the path to the excracted archive.

Use example:

    geoip_db = GeoipDB.get_instance()
    geo_info = geoip_db.get_info('178.153.16.203')
"""

import os
import re
import csv

from . import utils


GEOIP_DB_PATH = os.environ.get('GEOIP_DB_PATH', 'tmp/geoip.db')

IP_V4_PATTERN = re.compile(r'^\d{,3}\.\d{,3}\.\d{,3}\.\d{,3}$')


class GeoipDB:
    """
    GeoipDB implements a singleton that gives geo information about IP.
    It keeps opened file object and seeks for the necessary records using
    binary search algorithm.
    """

    _instance = None

    def __init__(self, path, block_size):
        self._file = open(path, 'rb')
        self._block_size = block_size
        self._size = os.path.getsize(path) // self._block_size

    def __del__(self):
        self._file.close()

    @classmethod
    def get_instance(cls):
        """
        Gets the instance or creates a new one as singleton.
        """
        if cls._instance is None:
            cls._instance = cls(GEOIP_DB_PATH, block_size=148)
        return cls._instance

    def get_info(self, ip):
        """
        Gets geo info about ip.
        """
        ip_bytes = utils.ip_to_bytes(ip)
        idx = self._find_idx(ip_bytes)
        block = self._get_block(idx)
        row = _unpack_block(block)
        return {
            'country': row[3],
            'region': row[4],
            'city': row[5],
        }

    def _get_block(self, idx):
        self._file.seek(idx * self._block_size)
        return self._file.read(self._block_size)

    def _find_idx(self, ip_bytes):
        idx = 0
        size = self._size
        while size > 0:
            block = self._get_block(idx + size // 2)
            if ip_bytes > block[4:8]:
                idx += size // 2 + 1
                size = size // 2 + size % 2 + 1
            else:
                size = size // 2
        return idx


def prepare_geoip_db(csv_path):
    """
    Transforms CSV geo database to binary format that can be successfully
    interpreted by GeoipDB.

    To run this function use manage.py:

        python manage.py prepare_geoip_db --path /path/to/csv/db.csv
    """
    with open(GEOIP_DB_PATH, 'wb') as geoip_db_file:
        with open(csv_path) as csv_file:
            for row in csv.reader(csv_file):
                # Use IPv4 only
                if IP_V4_PATTERN.match(row[0]):
                    row[6] = float(row[6])
                    row[7] = float(row[7])
                    block = _pack_block(*row)
                    geoip_db_file.write(block)


def _pack_block(ip_from, ip_to, continent, country, region, city,
                latitude, longitude):
    return b''.join((
        utils.ip_to_bytes(ip_from),
        utils.ip_to_bytes(ip_to),
        utils.str_to_bytes(continent, 2),
        utils.str_to_bytes(country, 2),
        utils.str_to_bytes(region, 40),
        utils.str_to_bytes(city, 80),
        utils.float_to_bytes(latitude),
        utils.float_to_bytes(longitude),
    ))


def _unpack_block(block):
    return (
        utils.ip_from_bytes(block[0:4]),
        utils.ip_from_bytes(block[4:8]),
        utils.str_from_bytes(block[8:10]),
        utils.str_from_bytes(block[10:12]),
        utils.str_from_bytes(block[12:52]),
        utils.str_from_bytes(block[52:132]),
        utils.float_from_bytes(block[132:140]),
        utils.float_from_bytes(block[140:148]),
    )
