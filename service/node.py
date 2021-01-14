"""
Node model is implemeted to store other nodes of proxy-finder to sync.
"""

import logging
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean

from .db import Base
from .utils import ensure_trailing_slash


class Node(Base):
    """
    Node model with the table in SQLite database.
    """

    __tablename__ = "node"

    url = Column(String, nullable=False, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    last_check_at = Column(DateTime)
    inactive_since = Column(DateTime)
    is_active = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"{self.url}"

    def as_dict(self):
        """
        Represents node object as dictionary.
        """
        return {
            key: getattr(self, key)
            for key in ('url', 'created_at', 'last_check_at')
        }

    def create(self, session):
        """
        Inserts node into the table.
        """
        if self.created_at is None:
            self.created_at = datetime.now()

        session.add(self)
        session.commit()

        logging.debug(f"Node {self} inserted")

    def exists(self, session):
        """
        Returns true if such node exists in the table.
        """
        return self.__class__.get(session, self.url) is not None

    def set_active(self, session):
        """
        Changes the state to active.
        """
        self.is_active = True
        self.last_check_at = datetime.now()
        self.inactive_since = None
        session.commit()

    def set_inactive(self, session):
        """
        Changes the state to inactive.
        """
        now = datetime.now()
        self.is_active = False
        self.last_check_at = now
        if self.inactive_since is None:
            self.inactive_since = now
        session.commit()

    @classmethod
    def get(cls, session, url):
        """
        Gets node from the table by its url.
        """
        return session.query(cls).filter_by(url=url).first()

    @classmethod
    def list_active(cls, session):
        """
        Returns list of active nodes.
        """
        return session.query(cls).filter_by(is_active=True)

    @classmethod
    def list_inactive(cls, session):
        """
        Returns list of inactive nodes.
        """
        return session.query(cls).filter_by(is_active=False)

    @classmethod
    def init_from_file(cls, session, path):
        """
        Inserts nodes from the file (given by path) into node table if they
        do not exist.
        """
        with open(path) as f:
            urls = map(str.strip, f.readlines())
            cls.insert_by_urls(session, urls)

    @classmethod
    def insert_by_urls(cls, session, urls):
        """
        Inserts nodes by given URLs if they do not exist.
        """
        for url in urls:
            node = cls(url=ensure_trailing_slash(url))
            if not node.exists(session):
                node.create(session)
