"""
A manager to run some commands of the service.

prepare_geoip_db - prepares binary geo database from CSV downloaded from
    https://db-ip.com/db/download/ip-to-city-lite
"""

import argparse

from service.geoip import prepare_geoip_db
from service.log import init_logging


init_logging()


def required(arg, message):
    """
    Prints message and stops execution if arg is None.
    """
    if arg is None:
        print(message)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare_geoip_db',))
    parser.add_argument('--path', '-p')
    args = parser.parse_args()

    if args.action == 'prepare_geoip_db':
        # Command prepare_geoip_db
        required(args.path, "Path to CSV required (parameter --path/-p).")
        prepare_geoip_db(args.path)
