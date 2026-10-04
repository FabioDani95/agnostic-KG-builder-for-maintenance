"""Run pytest with external networking denied; local UI tests retain loopback sockets."""
import socket
import sys

import pytest

connect = socket.socket.connect
connect_ex = socket.socket.connect_ex


def check(address):
    if isinstance(address, tuple) and address[0] not in {'127.0.0.1', '::1', 'localhost'}:
        raise AssertionError(f'Offline tests attempted external networking: {address[0]}')


def offline_connect(self, address):
    check(address)
    return connect(self, address)


def offline_connect_ex(self, address):
    check(address)
    return connect_ex(self, address)


socket.socket.connect = offline_connect
socket.socket.connect_ex = offline_connect_ex
if __name__ == '__main__':
    raise SystemExit(pytest.main(sys.argv[1:]))
