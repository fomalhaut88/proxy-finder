"""
ProxySearcher implements a search for proxies in multiple threads.

Use example:

    proxy_searcher = ProxySearcher(threads_num=1000)
    for proxy in proxy_searcher.search(count=10):
        ...
"""

import threading
from queue import Queue
from random import randint, choice

from .proxy import Proxy


class ProxySearcher:
    # Ports list to search for proxies
    ports = (8080, 3128)

    def __init__(self, threads_num):
        self._threads_num = threads_num

    def search(self, count=None):
        """
        A generator that yields found proxies. 'count' is the number of proxies
        to find. If 'count' is None, the generator is infinite.
        """
        # Queue to fill proxies by threads
        queue = Queue()

        # Stop event for the threads
        stop_event = threading.Event()

        # Threads to search for proxies
        threads = [
            threading.Thread(target=self._find_target,
                             args=(queue, stop_event))
            for _ in range(self._threads_num)
        ]

        # Start threads
        list(map(threading.Thread.start, threads))

        if count is not None:
            # Finite loop to search for proxies
            for _ in range(count):
                # Yield proxies that threads put into the queue
                yield queue.get(block=True)

            # Stop the threads by setting stop_event
            stop_event.set()

            # Wait until all threads are stopped
            list(map(threading.Thread.join, threads))

        else:
            # Infinite loop to search for proxies
            while True:
                # Yield proxies that threads put into the queue
                yield queue.get(block=True)

    def _find_target(self, queue, stop_event):
        while not stop_event.is_set():
            proxy = self._get_random_proxy()
            if proxy.check():
                queue.put(proxy)

    def _get_random_proxy(self):
        host = ".".join(str(randint(0, 255)) for _ in range(4))
        port = choice(self.ports)
        return Proxy(host=host, port=port)
