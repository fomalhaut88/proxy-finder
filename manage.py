"""
A manager to run some commands of the service.

prepare_geoip_db - prepares binary geo database from CSV downloaded from
    https://db-ip.com/db/download/ip-to-city-lite
"""

import os
import argparse
import logging

from service.geoip import prepare_geoip_db
from service.log import init_logging
from service.db import Session
from service.models import Node
from service import tasks


init_logging()


GEOIP_DB_DOWNLOAD_URL = os.environ.get('GEOIP_DB_DOWNLOAD_URL')
NODES_INIT_PATH = os.environ.get('NODES_INIT_PATH')


def required(arg, message):
    """
    Prints message and stops execution if arg is None.
    """
    if arg is None:
        logging.critical(message)
        print(message)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare_geoip_db', 'add_nodes',
                                           'run_task'))
    parser.add_argument('--url', '-u')
    parser.add_argument('--path', '-p')
    parser.add_argument('--task', '-t')
    args = parser.parse_args()

    if args.action == 'prepare_geoip_db':
        # Command prepare_geoip_db
        if args.url is None:
            logging.warning(
                f"Argument --url is not specified, using URL from " \
                f"GEOIP_DB_DOWNLOAD_URL: {GEOIP_DB_DOWNLOAD_URL}"
            )
            db_ip_url = GEOIP_DB_DOWNLOAD_URL
        else:
            db_ip_url = args.url
        required(db_ip_url, "No URL to download Geo DB")
        prepare_geoip_db(db_ip_url)

    elif args.action == 'add_nodes':
        # Command add_nodes
        if args.path is None:
            logging.warning(
                f"Argument --path is not specified, using path from " \
                f"NODES_INIT_PATH: {NODES_INIT_PATH}"
            )
            nodes_init_path = NODES_INIT_PATH
        else:
            nodes_init_path = args.path
        required(nodes_init_path, "No path to init nodes")
        session = Session()
        Node.init_from_file(session, nodes_init_path)

    elif args.action == 'run_task':
        required(args.task, "No task specified")
        task_cls = getattr(tasks, args.task)
        task_cls().run()
