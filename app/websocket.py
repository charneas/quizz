from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.game_rooms: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # Remove from game rooms
            for room in self.game_rooms.values():
                room.discard(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str, room_id: Optional[str] = None):
        if room_id and room_id in self.game_rooms:
            # Broadcast only to specific room
            for client_id in self.game_rooms[room_id]:
                await self.send_personal_message(message, client_id)
        else:
            # Broadcast to all connected clients
            for connection in self.active_connections.values():
                await connection.send_text(message)

    def join_room(self, client_id: str, room_id: str):
        if room_id not in self.game_rooms:
            self.game_rooms[room_id] = set()
        self.game_rooms[room_id].add(client_id)

    def leave_room(self, client_id: str, room_id: str):
        if room_id in self.game_rooms:
            self.game_rooms[room_id].discard(client_id)
            if not self.game_rooms[room_id]:
                del self.game_rooms[room_id]
