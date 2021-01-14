"""
Implements a Proxy model as a table in SQLite database (using SQLAlchemy)
"""

import os
import socket
import logging
import threading
from datetime import datetime

import requests
import requests.exceptions
from sqlalchemy import create_engine, Column, String, Integer, Float, \
                       DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .geoip import GeoipDB


# Path to SQLAlchemy database file
PROXY_DB_PATH = os.environ.get('PROXY_DB_PATH', 'tmp/proxy.db')

# URL to check proxy
TRY_URL = os.environ.get('TRY_URL', 'http://example.org/')

# Timeout for check proxy
CHECK_TIMEOUT = 3.0

# Coef to modify proxy score (see Proxy.score_up and Proxy.score_down)
SCORE_COEF = 0.25


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


class Proxy(Base):
    """
    Proxy model with the table in SQLite database.
    """

    __tablename__ = "proxy"

    host = Column(String, nullable=False, primary_key=True)
    port = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_check_at = Column(DateTime, nullable=False)
    inactive_since = Column(DateTime)
    is_active = Column(Boolean, nullable=False)
    country = Column(String, nullable=False)
    region = Column(String, nullable=False)
    city = Column(String, nullable=False)
    score = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint('host', 'port', name='host_port_uix'),
    )

    def __repr__(self):
        return f"{self.host}:{self.port}"

    def as_dict(self):
        """
        Represents proxy object as dictionary.
        """
        return {
            key: getattr(self, key)
            for key in ('host', 'port', 'created_at', 'country',
                        'region', 'city', 'score', 'last_check_at')
        }

    def create(self, session):
        """
        Fills NULL fields and inserts proxy into the table.
        """
        now = datetime.now()
        geo_info = GeoipDB.get_instance().get_info(self.host)

        if self.created_at is None:
            self.created_at = now

        if self.last_check_at is None:
            self.last_check_at = now

        if self.country is None:
            self.country = geo_info['country']

        if self.city is None:
            self.city = geo_info['city']

        if self.region is None:
            self.region = geo_info['region']

        session.add(self)
        session.commit()

        logging.debug(f"Proxy {self} inserted")

    def exists(self, session):
        """
        Returns true of such proxy exists in the table.
        """
        return self.__class__.get(session, self.host, self.port) is not None

    def check(self):
        """
        Checks the proxy for work. First, it checks the open port in the host.
        Second, it tries to request TRY_URL through proxy and to get the
        correct response.
        """
        return self._check_open_port() and self._try_proxy()

    def score_up(self):
        """
        Corrects proxy score up.
        """
        self.score = self.score * (1 - SCORE_COEF) + SCORE_COEF

    def score_down(self):
        """
        Corrects proxy score down.
        """
        self.score = self.score * (1 - SCORE_COEF)

    @classmethod
    def get(cls, session, host, port):
        """
        Gets proxy from the table by its host and port.
        """
        return session.query(cls).filter_by(host=host, port=port).first()

    @classmethod
    def list_active(cls, session):
        """
        Returns list of active proxies.
        """
        return session.query(cls).filter_by(is_active=True)

    @classmethod
    def list_inactive(cls, session):
        """
        Returns list of inactive proxies.
        """
        return session.query(cls).filter_by(is_active=False)

    def _check_open_port(self):
        logging.debug(f"Checking open port for {self}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((self.host, self.port))
        sock.close()
        return result == 0

    def _try_proxy(self):
        logging.debug(f"Trying proxy {self}")
        proxies = {"https": f"http://{self.host}:{self.port}"}
        try:
            with requests.get(TRY_URL, proxies=proxies,
                              timeout=CHECK_TIMEOUT) as response:
                return response.status_code == 200
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout) as exc:
            return False


# Encure the table for Proxy in the database
Base.metadata.create_all(engine)
