import socket
import struct
import utils
from scheduler import scheduler

# TODO: We currently bind the UDP socket to a particular interface by binding the socket to the
#       IPv4 address of the interface.
#       - Also need to support IPv6
#       - What about unnumbered interfaces? Can we support those (using the address of the loopback,
#         as the source address, but only receiving packets on the specified interface)? I would
#         like to use SO_BINDTODEVICE but that is not portable (available on Linux but not MacOS X)

class MulticastReceiveHandler:

    MAXIMUM_MESSAGE_SIZE = 65535

    def __init__(self, interface_name, multicast_address, port, loopback, receive_function):
        self._interface_ipv4_address = utils.interface_ipv4_address(interface_name)
        self._multicast_address = multicast_address
        self._port = port
        self._receive_function = receive_function
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)     # TODO: Not supported on all OSs
        self._sock.bind((multicast_address, port))   # TODO: Is this correct? Do we bind to the multicast address?
        req = struct.pack("=4s4s", socket.inet_aton(multicast_address), socket.inet_aton(self._interface_ipv4_address))  # TODO: Is this right? It appears to work.
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)
        if loopback:
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        scheduler.register_handler(self, True, False)

    def close(self):
        scheduler.unregister_handler(self)
        self._sock.close()

    def socket(self):
        return self._sock

    def ready_to_read(self):
        message, from_address_and_port = self._sock.recvfrom(self.MAXIMUM_MESSAGE_SIZE)
        self._receive_function(message, from_address_and_port)
