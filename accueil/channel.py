
from attrs import define, field
from sanic import Websocket
from sanic.exceptions import WebsocketClosed

@define(repr=False)
class Channel:
    name: str = field()
    __subs: list[Websocket] = field()
    
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