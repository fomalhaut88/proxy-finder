"""
There are tasks to search, check and update proxies in the database.
"""

import os
import logging
from datetime import datetime, timedelta

import requests

from .proxy_searcher import ProxySearcher
from .db import Session
from .models import Proxy, Node
from .task_manager import TaskManager, BaseTask, PeriodicTask
from .log import init_logging
from .thread_pool import ThreadPool
from .net_blacklist import NetBlacklist


# The number of threads to search for proxies in ProxySearcher
PROXY_SEARCH_THREADS = int(os.environ.get('PROXY_SEARCH_THREADS', '100'))

# Path to nets blacklist
NET_BLACKLIST = os.environ.get('NET_BLACKLIST', '')

# URL of deployed instance
INSTANCE_URL = os.environ.get('INSTANCE_URL', '')


init_logging()
task_manager = TaskManager()


class SessionMixin:
    """
    Mixin to add session for the task.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = Session()


@task_manager.register
class ProxySearchTask(SessionMixin, BaseTask):
    """
    Task to search for proxies with ProxySearcher.
    """

    def run(self):
        logging.info(
            f"Start ProxySearcher with {PROXY_SEARCH_THREADS} threads"
        )

        net_blacklist = NetBlacklist.from_file(NET_BLACKLIST) \
            if NET_BLACKLIST else None
        proxy_searcher = ProxySearcher(PROXY_SEARCH_THREADS, net_blacklist)

        for proxy in proxy_searcher.search():
            logging.info(f"Found proxy {proxy}")
            if not proxy.exists(self.session):
                proxy.is_active = True
                proxy.create(self.session)
                logging.info(f"Created proxy {proxy}")


@task_manager.register
class UpdateActiveProxyTask(SessionMixin, PeriodicTask):
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
class UpdateInactiveProxyTask(SessionMixin, PeriodicTask):
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


@task_manager.register
class SyncNodesTask(SessionMixin, PeriodicTask):
    """
    Sync proxies between nodes. It includes requests for nodes and proxies at
    other nodes.
    """

    timeout = 60.0
    threads_num = 100
    update_delta = timedelta(hours=1)

    def handle(self):
        nodes = self._prepare_nodes_to_sync()
        self._sync_nodes(nodes)
        self._sync_proxies(nodes)

    def _prepare_nodes_to_sync(self):
        now = datetime.now()
        nodes = list(self.session.query(Node))
        nodes_active = self._filter_active(nodes, now)
        nodes_inactive = self._filter_inactive(nodes, now)
        return nodes_active | nodes_inactive

    def _sync_nodes(self, nodes):
        pool = ThreadPool(self.threads_num)
        result = pool.map(self._request_nodes, nodes)
        for node, nd_list in zip(nodes, result):
            if nd_list is not None:
                for nd in nd_list:
                    if nd not in nodes and not nd.exists(self.session):
                        nd.create(self.session)
                node.set_active(self.session)
            else:
                node.set_inactive(self.session)

    def _sync_proxies(self, nodes):
        proxy_set_local = set(self.session.query(Proxy))
        pool = ThreadPool(self.threads_num)
        result = pool.map(self._request_proxies, nodes)
        for proxy_list in result:
            if proxy_list is not None:
                for proxy in proxy_list:
                    if proxy not in proxy_set_local:
                        if not proxy.exists(self.session):
                            proxy.is_active = True
                            proxy.create(self.session)

    def _filter_active(self, nodes, now):
        return set(filter(
            lambda node: node.is_active and
                         now - node.last_check_at > self.update_delta,
            nodes
        ))

    def _filter_inactive(self, nodes, now):
        return set(filter(
            lambda node: not node.is_active and (
                node.last_check_at is None or
                now - node.last_check_at > \
                    node.last_check_at - node.inactive_since
            ),
            nodes
        ))

    def _request_nodes(self, node):
        url = os.path.join(node.url, 'nodes')

        if INSTANCE_URL:
            response = requests.post(url, data={'url': INSTANCE_URL})
        else:
            response = requests.get(url)

        if response.status_code == 200:
            result = [
                Node(url=item['url'])
                for item in response.json()['result']
            ]
        else:
            result = None

        response.close()

        return result

    def _request_proxies(self, node):
        url = os.path.join(node.url, 'list')

        with requests.get(url) as response:
            if response.status_code == 200:
                result = response.json()['result']
                return [
                    Proxy(host=item['host'], port=item['port'])
                    for item in result
                ]

        return None
