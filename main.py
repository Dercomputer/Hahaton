from fastapi import FastAPI, HTTPException, WebSocket
import uuid
import json
import os
from dataclasses import dataclass
from multiprocessing.pool import ThreadPool
import barcodenumber

app = FastAPI()
pool = ThreadPool(processes=os.cpu_count())


@dataclass
class Item:
    name: str
    vendor: str
    price: int
    description: str
    barcode: int
    article: int
    discount: int


@dataclass
class User:
    id: str
    items: [Item]
    subscriber = None

    def start(self):
        pool.map_async(
            self.__handle_item__,
            self.items,
            callback=lambda: self.subscriber["completed"]()
        )

    def subscribe(self, on_error, on_warning, on_completed):
        self.subscriber = {
            "error": on_error,
            "warning": on_warning,
            "completed": on_completed
        }

    def __add_error__(self, field: str, error: str):
        self.subscriber["error"](field, error)

    def __add_warning__(self, field: str, warning: str):
        self.subscriber["warning"](field, warning)

    def __handle_item__(self, item: Item):
        if 60 < item.discount < 85:
            self.__add_warning__("discount", "Высокая скидка")
        if item.discount > 85:
            self.__add_error__("discount", "Черезмерная скидка")
        if not item.description:
            self.__add_error__("descriprion", "Нет описания")
        if not barcodenumber.check_code('ean13', item.barcode):
            self.__add_error__("barcode", "Не валидный баркод")
        if len(str(item.article)) != 5:
            self.__add_error__("article", "Артикул невалиден")
        if item.price < 10:
            self.__add_error__("price", "Слишком низкая цена")


users = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/room/{room_id}")
async def websocket_room(*, websocket: WebSocket, room_id: str):
    await manager.connect(websocket)
    if room_id not in users:
        manager.disconnect(websocket)
        await manager.broadcast(f"Room ${room_id} is not created")

    user = users[room_id]
    user.subscribe(
        lambda field, error: manager.send_personal_message(json.dump({"type": "error", "field": field, "error": error}),
                                                           websocket),
        lambda field, warning: manager.send_personal_message(
            json.dump({"type": "warning", "field": field, "error": warning}), websocket),
        lambda: manager.disconnect(websocket)
    )
    user.start()


@app.post("/uploadfile/")
async def upload_file(string: str):
    try:
        contents = string
        data = json.loads(contents)
        user = User(
            str(uuid.uuid4()),
            list(map(lambda item: Item(
                item["name"],
                item["vendor"],
                item["price"],
                item["description"],
                item["barcode"],
                item["article"],
                item["discount"]
            ), data)))
        users[user.id] = user
        return {"id": user.id}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
