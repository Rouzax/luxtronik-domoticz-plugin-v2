"""Characterization tests for connection.py (ConnectionManager).

These lock in CURRENT behavior so future refactors are safe to verify. They
are offline-only: no real socket I/O, no live heat pump required. The write
safety guard is exercised directly (no live connection needed) since it is
checked before any socket I/O; a fake truthy `_socket` is enough to get past
the "no connection" early return.
"""

import context
from addresses import SocketCommand
from connection import ConnectionManager


class RecLogger:
    def __init__(self):
        self.errors = []

    def log(self, *a, **k):
        pass

    def error(self, msg, *a, **k):
        self.errors.append(msg)


def setup_function():
    context.logger = RecLogger()


def test_enable_disable_writes_gates_addresses():
    c = ConnectionManager("h", 1)
    assert c._write_enabled is False
    c.enable_writes([1, 3, 4])
    assert c._write_enabled and c._allowed_write_addresses == {1, 3, 4}
    c.disable_writes()
    assert c._write_enabled is False
    assert c._allowed_write_addresses == set()


def test_send_command_returns_none_without_connection():
    # No socket at all -- send_command bails out before the write guard.
    c = ConnectionManager("h", 1)
    ok = c.send_command(SocketCommand.WRITE_PARAMS, address=1, value=5)
    assert ok is None
    assert context.logger.errors == []  # guard never reached, nothing logged


def test_write_blocked_when_disabled():
    c = ConnectionManager("h", 1)
    # A truthy dummy socket gets us past the "no connection" check; the write
    # guard itself returns before any socket I/O is attempted.
    c._socket = object()
    ok = c.send_command(SocketCommand.WRITE_PARAMS, address=1, value=5)
    assert ok is None
    assert any("Writes not enabled" in e for e in context.logger.errors)


def test_write_blocked_when_address_not_allowed():
    c = ConnectionManager("h", 1)
    c._socket = object()
    c.enable_writes([1])
    ok = c.send_command(SocketCommand.WRITE_PARAMS, address=99, value=5)
    assert ok is None
    assert any("not in allowed list" in e for e in context.logger.errors)


def test_recv_exact_reassembles_chunks():
    c = ConnectionManager("h", 1)

    class FakeSock:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def recv(self, n):
            return self.chunks.pop(0)

    c._socket = FakeSock([b"ab", b"cd", b"ef"])
    assert c._recv_exact(6) == b"abcdef"


def test_recv_exact_raises_on_closed_connection():
    c = ConnectionManager("h", 1)

    class FakeSock:
        def __init__(self, chunks):
            self.chunks = list(chunks)

        def recv(self, n):
            return self.chunks.pop(0)

    c._socket = FakeSock([b"ab", b""])
    try:
        c._recv_exact(6)
        raised = False
    except OSError:
        raised = True
    assert raised
