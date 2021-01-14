"""
There are tasks to search, check and update proxies in the database.
"""

import os
import logging
from datetime import datetime, timedelta

from .proxy_searcher import ProxySearcher
from .proxy import Proxy, Session
from .task_manager import TaskManager, BaseTask, PeriodicTask
from .log import init_logging
from .thread_pool import ThreadPool


# The number of threads to search for proxies in ProxySearcher
PROXY_SEARCH_THREADS = int(os.environ.get('PROXY_SEARCH_THREADS', '100'))


init_logging()
task_manager = TaskManager()


class ProxyTaskMixin:
    """
    Mixin to add session for the task.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = Session()


@task_manager.register
class ProxySearchTask(ProxyTaskMixin, BaseTask):
    """
    Task to search for proxies with ProxySearcher.
    """

    def run(self):
        logging.info(
            f"Start ProxySearcher with {PROXY_SEARCH_THREADS} threads"
        )

        proxy_searcher = ProxySearcher(PROXY_SEARCH_THREADS)

        for proxy in proxy_searcher.search():
            logging.info(f"Found proxy {proxy}")
            if not proxy.exists(self.session):
                proxy.is_active = True
                proxy.create(self.session)
                logging.info(f"Created proxy {proxy}")


@task_manager.register
class UpdateActiveProxyTask(ProxyTaskMixin, PeriodicTask):
    """
    Task to check and update active proxies.
    """

    timeout = 60.0
    threads_num = 100
    update_delta = timedelta(hours=1)

    def handle(self):
        now = datetime.now()
        proxy_list = [
            proxy for proxy in Proxy.list_active(self.session)
            if now - proxy.last_check_at > self.update_delta
        ]

        pool = ThreadPool(self.threads_num)
        result = pool.map(Proxy.check, proxy_list)

        for proxy, success in zip(proxy_list, result):
            if success:
                logging.info(f"Successfully checked proxy {proxy}")
                proxy.score_up()
            else:
                logging.info(f"Failed proxy {proxy}")
                proxy.is_active = False
                proxy.inactive_since = now
                proxy.score_down()
            proxy.last_check_at = now
            self.session.commit()
            logging.info(f"Proxy {proxy} updated")


@task_manager.register
class UpdateInactiveProxyTask(ProxyTaskMixin, PeriodicTask):
    """
    Task to check and update inactive proxies.
    """

    timeout = 60.0
    threads_num = 100

    def handle(self):
        now = datetime.now()
        proxy_list = [
            proxy for proxy in Proxy.list_inactive(self.session)
            if now - proxy.last_check_at > \
                proxy.last_check_at - proxy.inactive_since
        ]

        pool = ThreadPool(self.threads_num)
        result = pool.map(Proxy.check, proxy_list)

        for proxy, success in zip(proxy_list, result):
            if success:
                logging.info(f"Successfully checked proxy {proxy}")
                proxy.is_active = True
                proxy.inactive_since = None
                proxy.score_up()
            else:
                logging.info(f"Failed proxy {proxy}")
                proxy.score_down()
            proxy.last_check_at = now
            self.session.commit()
            logging.info(f"Proxy {proxy} updated")
