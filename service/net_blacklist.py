"""
NetBlacklist implements a list of networks that can check an ip in any of
the networks fast.

Example:

    nb = NetBlacklist()

    nb.add_subnetwork('192.168.0.1/24')
    nb.add_subnetwork('192.168.5.1/25')
    nb.add_subnetwork('192.168.1.1/24')

    print('192.168.0.25' in nb)
"""

from operator import attrgetter

from .utils import ip_to_int, binary_search


class Net:
    """
    Net implements a network that stores the range of IP address
    (in integer representation).
    """

    def __init__(self, int_from, int_to):
        self.int_from = int_from
        self.int_to = int_to

    def __len__(self):
        """
        The number of addresses in the net.
        """
        return self.int_to - self.int_from + 1

    def __contains__(self, ip_int):
        """
        Checks if IP (given as integer) is in the net.
        """
        return ip_int >= self.int_from and ip_int <= self.int_to

    @classmethod
    def from_subnetwork(cls, subnetwork):
        """
        Creates a network object from a string (example: '192.168.0.1/24').
        """
        ip, bits_str = subnetwork.split('/', 1)
        bits = 32 - int(bits_str)

        int_from = ip_to_int(ip)
        int_from >>= bits
        int_from <<= bits

        int_to = int_from + 2**bits - 1

        return cls(int_from, int_to)


class NetBlacklist:
    """
    List of networks that uses binary search to check if an IP belongs to any
    of the stored nets. It is supposed the networks added have no
    intersections, otherwise the work can be incorrect.
    """

    def __init__(self):
        self._nets = []

    def __len__(self):
        """
        Total number of IP of all networks stored in the list.
        """
        return sum(map(len, self._nets))

    def __contains__(self, ip):
        """
        Checks IP in any of the networks.
        """
        ip_int = ip_to_int(ip)
        idx = binary_search(self._nets, ip_int, attrgetter('int_to'))
        if idx < len(self._nets):
            return ip_int in self._nets[idx]
        else:
            return False

    def add_subnetwork(self, subnetwork):
        """
        Adds a network to the list.
        """
        net = Net.from_subnetwork(subnetwork)
        idx = binary_search(self._nets, net.int_from, attrgetter('int_from'))
        self._nets.insert(idx, net)

    @classmethod
    def from_file(cls, path):
        """
        Creates NetBlacklist from the networks listed in a file given by path.
        """
        obj = cls()
        with open(path) as f:
            for subnetwork in f:
                obj.add_subnetwork(subnetwork)
        return obj
