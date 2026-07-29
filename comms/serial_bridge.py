import asyncio
import json
import structlog
import serial_asyncio

log = structlog.get_logger()


class SerialBridge:
    def __init__(self, port: str, baud: int = 9600, timeout: float = 0.2):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._writer: asyncio.StreamWriter | None = None
        self._reader: asyncio.StreamReader | None = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self):
        try:
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self.port, baudrate=self.baud
            )
            self._connected = True
            log.info("serial_connected", port=self.port, baud=self.baud)
        except Exception as e:
            log.error("serial_connect_failed", error=str(e))
            self._connected = False

    async def send(self, command: dict) -> dict | None:
        if not self._connected:
            log.warning("serial_not_connected")
            return None
        async with self._lock:
            payload = json.dumps(command) + "\n"
            self._writer.write(payload.encode())
            await self._writer.drain()
            log.debug("serial_sent", command=command)
        ack = await self._read_ack()
        return ack

    async def _read_ack(self) -> dict | None:
        try:
            line = await asyncio.wait_for(self._reader.readline(), timeout=self.timeout)
            if line:
                data = json.loads(line.decode().strip())
                log.debug("serial_ack", ack=data)
                return data
        except asyncio.TimeoutError:
            log.debug("serial_ack_timeout")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            log.warning("serial_ack_parse_error", error=str(e))
        return None

    async def ping(self) -> bool:
        ack = await self.send({"cmd": "PING"})
        return ack is not None and ack.get("ack") == "OK"

    async def close(self):
        self._connected = False
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        log.info("serial_disconnected")

    @property
    def connected(self) -> bool:
        return self._connected
