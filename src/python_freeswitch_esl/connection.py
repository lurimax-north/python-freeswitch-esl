import asyncio
from collections import defaultdict
import json
import logging
import re
from typing import AsyncGenerator
from . import events

from collections.abc import Callable

log = logging.getLogger(__name__)


class ESLClient:
    REFRESH_INTERVAL = 0.1

    def __init__(
        self,
        host: str,
        port: int = 8021,
        password: str = "",
        subscribed_events: list = None,
        event_callbacks: dict = defaultdict[str, list|Callable](list),
    ):
        self.password = password
        self.host = host
        self.port = port
        self.subscribed_events = subscribed_events or []

        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.is_connected: bool = False
        self.is_authed: bool = False

        self.event_callbacks: defaultdict[str, list[Callable]] = defaultdict(list) # type: ignore
        self._update_subscribed_events(event_callbacks)

    def _update_subscribed_events(self, event_callbacks: dict):
        """
        Since events can be passes as both a single event or a list of event,
        We just need to make sure our callbacks are always a list.
        """
        for event, funcs in event_callbacks.items():
            if isinstance(funcs, list):
                self.event_callbacks[event] = funcs
            else:
                print(self.event_callbacks)
                self.event_callbacks[event].append(funcs)

    async def initialize(self):
        self._update_subscribed_events(self.event_callbacks)
        await self.connect()
        if self.password:
            await self.auth()
        await self.subscribe()

    async def connect(self):
        log.debug("%s:%s", self.host, self.port)
        self.reader, self.writer = await asyncio.open_connection(
            self.host,
            self.port,
        )
        await self.writer.drain()
        data = await self.reader.readuntil(b"\n\n")
        log.debug("Connection response: %s", data.decode())
        # TODO: Verify what response is used for non authed servers
        if b"Content-Type: auth/request\n\n" not in data:
            log.error("Connection failed: %s", data.decode())
            raise OSError("Connection failed")
        else:
            log.debug("Connected to %s:%s", self.host, self.port)
            self.is_connected = True

    async def auth(self):
        self.writer.write(f"auth {self.password}\n\n".encode())
        await self.writer.drain()
        data = await self.reader.readuntil(b"\n\n")
        log.debug("Authentication response: %s", data.decode())
        if b"+OK" not in data:
            log.error("Authentication failed: %s", data.decode())
            raise PermissionError("Authentication failed")
        else:
            self.is_authed = True
            log.debug("Authenticated to %s:%s", self.host, self.port)

    def add_event_callback(self, event: str, callback: Callable):
        self.event_callbacks[event].append(callback)

    async def subscribe(self):
        if self.subscribed_events:
            self.writer.write(
                f"event json {' '.join(self.subscribed_events)}\n\n".encode()
            )
        else:
            self.writer.write(b"event json all\n\n")
        await self.writer.drain()
        data = await self.reader.readuntil(b"\n\n")
        log.debug("%s", data.decode())

    async def run(self):
        await self.initialize()
        async for _ in self.loop():
            continue

    async def loop(self) -> AsyncGenerator[events.Event]:
        while True:
            data = await self.reader.readuntil(b"\n\n")
            data = data.decode()
            log.debug("%s", data)
            data.split("\n")
            # Check if data looks like json
            if data.startswith("{"):
                try:
                    headers = json.loads(re.findall(r"{.*}", data)[0])
                    if not headers:
                        log.warning("No data found: %s", data)
                        continue
                    event = events.EventType(
                        headers=headers, body=data, content_length=0
                    )
                    log.debug("Event: %s", event)

                    # Handle the event if required
                    print("Self event callbacks: ", self.event_callbacks)

                    for func in self.event_callbacks.get(
                        event.headers["Event-Name"], []
                    ):
                        func(event)

                    yield event

                except json.JSONDecodeError:
                    log.error("Unable to parse message %s", data)
                    continue
            else:
                log.warning("Unexpected data: %s", data)
            await asyncio.sleep(self.REFRESH_INTERVAL)

    async def send_command(self, message: str):
        self.writer.write(f"{message}\n\n".encode())
        await self.writer.drain()

    async def api(self, command: str):
        await self.send_command(f"api {command}")
