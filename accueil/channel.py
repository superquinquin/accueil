
from attrs import define, field
from sanic import Websocket
from sanic.exceptions import WebsocketClosed

class Channel:
    name: str
    __subs: list[Websocket]

    def __init__(self, name: str, subs: list[Websocket] | None = None) -> None:
        self.name = name
        self.__subs = subs or []

    def __repr__(self) -> str:
        return f"Channel {self.name}: {self.size} subbed listeners."

    @property
    def subs(self) -> list[Websocket]:
        return self.__subs

    @property
    def size(self) -> int:
        return len(self.subs)

    def subscribe(self, socket: Websocket) -> None:
        self.__subs.append(socket)

    def unsubscribe(self, socket: Websocket) -> None:
        self.__subs.pop(self.subs.index(socket))

    async def broadcast(self, data: str) -> None:
        closed = []
        for socket in self.subs:
            try:
                await socket.send(data)
            except WebsocketClosed:
                closed.append(socket)
        [self.unsubscribe(socket) for socket in closed]
