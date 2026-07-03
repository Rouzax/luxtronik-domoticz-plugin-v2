"""Socket connection management for the Luxtronik plugin.

Extracted from plugin.py. Does not import DomoticzEx or plugin.
Shared runtime state (the live logger) is accessed via the context module.
"""

import contextlib
import socket
import struct
from typing import Dict, List, Optional, Tuple

import context
from addresses import SocketCommand
from context import DebugLevel


class ConnectionManager:
    """Manages socket connections to the Luxtronik controller.

    SECURITY NOTE: The Luxtronik protocol uses plain TCP without encryption
    or authentication. This is a hardware limitation. Ensure your heat pump
    is on a trusted network and not exposed to the internet.

    SAFETY: This class includes protection against unintended writes.
    Write operations require explicit validation before sending.
    """

    TIMEOUT = 5
    MAX_ATTEMPTS = 2  # 1 initial attempt + 1 retry
    MAX_ARRAY_LENGTH = 2000  # Sanity limit for protocol response arrays

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._write_enabled = False  # Write protection flag
        self._allowed_write_addresses: set = set()  # Addresses that can be written

    def enable_writes(self, allowed_addresses: List[int]) -> None:
        """Enable write operations for specific addresses only.

        This must be called during plugin initialization to allow any writes.
        """
        self._allowed_write_addresses = set(allowed_addresses)
        self._write_enabled = True
        context.logger.log(f"Writes enabled for addresses: {allowed_addresses}", DebugLevel.BASIC)

    def disable_writes(self) -> None:
        """Disable all write operations (safety lockout)."""
        self._write_enabled = False
        self._allowed_write_addresses.clear()
        context.logger.log("Writes disabled", DebugLevel.BASIC)

    def connect(self) -> bool:
        """Establish connection to the controller."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.TIMEOUT)
            self._socket.connect((self.host, self.port))
            context.logger.log(f"Connected to {self.host}:{self.port}", DebugLevel.COMMS)
            return True
        except socket.error as e:
            context.logger.error(f"Connection failed to {self.host}:{self.port}", exc=e)
            self.close()
            return False
        except Exception as e:
            context.logger.error(f"Unexpected connection error to {self.host}:{self.port}", exc=e)
            self.close()
            return False

    def close(self) -> None:
        """Close the connection."""
        if self._socket:
            with contextlib.suppress(Exception):
                self._socket.close()
            self._socket = None

    def _recv_exact(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from the socket.

        TCP does not guarantee that recv() returns all requested bytes in a
        single call. This method loops until the full payload is received,
        preventing silent data corruption from partial reads.

        Raises:
            socket.error: If the connection is closed before all bytes arrive
        """
        data = b""
        while len(data) < num_bytes:
            chunk = self._socket.recv(num_bytes - len(data))
            if not chunk:
                raise socket.error("Connection closed during receive")
            data += chunk
        return data

    def send_command(
        self, command: int, address: int = 0, value: int = 0
    ) -> Optional[Tuple[int, int, int, List[int]]]:
        """Send a command and receive response.

        SAFETY: Write commands (WRITE_PARAMS) are blocked unless:
        1. Writes are enabled via enable_writes()
        2. The address is in the allowed list
        """
        if not self._socket:
            return None

        # SAFETY CHECK: Block unauthorized write attempts
        if command == SocketCommand.WRITE_PARAMS:
            if not self._write_enabled:
                context.logger.error("WRITE BLOCKED: Writes not enabled")
                return None
            if address not in self._allowed_write_addresses:
                context.logger.error(f"WRITE BLOCKED: Address {address} not in allowed list")
                return None
            context.logger.log(
                f"WRITE AUTHORIZED: address={address}, value={value}", DebugLevel.BASIC
            )

        try:
            # Send command and address
            self._socket.send(struct.pack("!i", command))
            self._socket.send(struct.pack("!i", address))

            # Send value for write commands
            if command == SocketCommand.WRITE_PARAMS:
                self._socket.send(struct.pack("!i", value))

            # Verify command echo
            received = struct.unpack("!i", self._recv_exact(4))[0]
            if received != command:
                raise Exception(f"Command verification failed: sent {command}, received {received}")

            # Process response
            stat = 0
            length = 0
            data_list = []

            if command == SocketCommand.READ_PARAMS:
                length = struct.unpack("!i", self._recv_exact(4))[0]
            elif command == SocketCommand.READ_CALCUL:
                stat = struct.unpack("!i", self._recv_exact(4))[0]
                length = struct.unpack("!i", self._recv_exact(4))[0]

            if length > self.MAX_ARRAY_LENGTH:
                raise Exception(
                    f"Protocol response length {length} exceeds maximum {self.MAX_ARRAY_LENGTH}"
                )

            if length > 0:
                data_list = [struct.unpack("!i", self._recv_exact(4))[0] for _ in range(length)]

            context.logger.log(
                f"{SocketCommand.get_name(command)}: Received {length} values", DebugLevel.COMMS
            )
            return command, stat, length, data_list

        except socket.error as e:
            context.logger.error("Socket error during command", exc=e)
            return None
        except Exception as e:
            context.logger.error("Command failed", exc=e)
            return None

    def execute_with_retry(
        self, command: int, address: int = 0, value: int = 0
    ) -> Tuple[int, int, int, List[int]]:
        """Execute a single command with retry logic.

        Opens a connection, sends one command, then closes. Used for
        single-command operations like writes.
        """
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if self.connect():
                    result = self.send_command(command, address, value)
                    if result:
                        return result
            except socket.error as e:
                if attempt == 0:
                    context.logger.log(
                        f"Socket error (retrying): {type(e).__name__}: {e}", DebugLevel.COMMS
                    )
            finally:
                self.close()

        context.logger.error(f"Command failed after {self.MAX_ATTEMPTS} attempts")
        return command, 0, 0, []

    def execute_batch_with_retry(
        self, commands: List[Tuple[int, int, int]]
    ) -> Dict[int, Tuple[int, int, int, List[int]]]:
        """Execute multiple commands on a single connection with retry logic.

        The Luxtronik controller supports sequential commands on one TCP
        connection. This avoids redundant TCP handshakes when multiple
        read commands are needed (e.g., READ_CALCUL + READ_PARAMS).

        Args:
            commands: List of (command, address, value) tuples to execute.

        Returns:
            Dict mapping command code to its (command, stat, length, data_list)
            result. Failed commands are omitted from the dict.
        """
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if not self.connect():
                    continue

                results: Dict[int, Tuple[int, int, int, List[int]]] = {}
                all_ok = True

                for command, address, value in commands:
                    result = self.send_command(command, address, value)
                    if result:
                        results[command] = result
                    else:
                        all_ok = False
                        break  # Connection likely broken, retry from scratch

                if all_ok:
                    return results

            except socket.error as e:
                if attempt == 0:
                    context.logger.log(
                        f"Socket error during batch (retrying): {type(e).__name__}: {e}",
                        DebugLevel.COMMS,
                    )
            finally:
                self.close()

        context.logger.error(f"Batch command failed after {self.MAX_ATTEMPTS} attempts")
        return {}
