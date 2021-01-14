from unittest import TestCase

from .proxy_searcher import ProxySearcher
from .models import Proxy
from .thread_pool import ThreadPool
from .utils import binary_search, ip_to_int, int_to_ip
from .net_blacklist import NetBlacklist


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


class UtilsTest(TestCase):
    def test_binary_search(self):
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 8),
            2
        )
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 2),
            0
        )
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 23),
            4
        )
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 0),
            0
        )
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 3),
            1
        )
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 22),
            4
        )
        self.assertEqual(
            binary_search([2, 4, 8, 10, 23], 25),
            5
        )
        self.assertEqual(
            binary_search([], 22),
            0
        )
        self.assertEqual(
            binary_search([2], 22),
            1
        )
        self.assertEqual(
            binary_search([2], 0),
            0
        )
        self.assertEqual(
            binary_search([2], 2),
            0
        )

    def test_ip_to_int(self):
        self.assertEqual(ip_to_int('192.168.0.1'), 3232235521)

    def test_int_to_ip(self):
        self.assertEqual(int_to_ip(3232235521), '192.168.0.1')


class NetBlacklistTest(TestCase):
    def test(self):
        nb = NetBlacklist()

        nb.add_subnetwork('192.168.0.1/24')
        nb.add_subnetwork('192.168.5.1/25')
        nb.add_subnetwork('192.168.1.1/24')

        self.assertEqual(len(nb), 640)

        self.assertTrue('192.168.0.25' in nb)
        self.assertTrue('192.168.0.225' in nb)
        self.assertTrue('192.168.0.0' in nb)
        self.assertTrue('192.168.1.25' in nb)
        self.assertTrue('192.168.1.225' in nb)
        self.assertTrue('192.168.5.25' in nb)
        self.assertFalse('192.168.5.225' in nb)
        self.assertFalse('192.168.4.225' in nb)
        self.assertFalse('192.168.34.225' in nb)
        self.assertFalse('192.167.0.1' in nb)
