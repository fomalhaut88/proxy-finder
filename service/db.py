import os
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# Path to SQLAlchemy database file
PROXY_DB_PATH = os.environ.get('PROXY_DB_PATH', 'tmp/proxy.db')


engine = create_engine(f'sqlite:///{PROXY_DB_PATH}')
Session = sessionmaker(bind=engine)
Base = declarative_base()


class SessionThreadPool:
    """
    It is a pool of sessions for each theard. It contains the method 'get'
    that returns a session of the current thread or create a new one if it
    does not exist yet.
    """

    def __init__(self):
        self._pool = {}

    def get(self):
        """
        Returns the session of the current thread. It creates a new session
        if it has not been created before.
        """
        tid = threading.get_ident()
        if tid not in self._pool:
            self._pool[tid] = Session()
        return self._pool[tid]
