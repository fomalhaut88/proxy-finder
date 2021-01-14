from unittest import TestCase

from .proxy_searcher import ProxySearcher
from .proxy import Proxy
from .thread_pool import ThreadPool


class ProxySearcherTest(TestCase):
    @classmethod
    def setUpClass(cls):
        def _try_proxy(proxy):
            return proxy.host.endswith('5')

        cls._old_proxy_try_proxy = Proxy._try_proxy
        Proxy._try_proxy = _try_proxy

    @classmethod
    def tearDownClass(cls):
        Proxy._try_proxy = cls._old_proxy_try_proxy

    def test(self):
        proxy_searcher = ProxySearcher(1000)
        proxy_list = proxy_searcher.search(count=3)
        self.assertTrue(all(proxy.host.endswith('5') for proxy in proxy_list))


class ThreadPoolTest(TestCase):
    def test(self):
        thread_pool = ThreadPool(10)
        result = thread_pool.map(lambda x: x**2, [1, 2, 3])
        self.assertListEqual(result, [1, 4, 9])
