#!/usr/bin/env python3
# _*_coding:utf-8_*_
from fastapi import (
    FastAPI,
    HTTPException,
    Path,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import plistlib
import netifaces
import json
import os
from pathlib import Path
from pathvalidate import is_valid_filename, sanitize_filename
import asyncio
import appdirs
from send2trash import send2trash
import signal
import time
from libs.markdown_tts_processor import MarkdownTTSProcessor

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processor = MarkdownTTSProcessor()
database = {}
id_counter = 1


async def handle_message(websocket: WebSocket, clientID: int, message_text: str) -> str:
    global id_counter
    message = json.loads(message_text)
    type = message["type"]
    if type == "text":
        text = message["data"]
        text_id=message["text_id"]
        # id = "id-" + str(id_counter)
        # id_counter += 1
        database[text_id] = processor.process(text)
        message = {
            "type": "parse_result",
            "data": {"text_id": text_id, "result": database[text_id]},
        }
        print(message)
        await websocket.send_text(json.dumps(message))
    elif type == "sentence":
        id = message["data"]["text_id"]
        sentence_id = message["data"]["sentence_id"]
        print(database[id][sentence_id])


@app.websocket("/ws/aichat/{clientID}")
async def websocketEndpointVarchive(websocket: WebSocket, clientID: int):
    await websocket.accept()

    async def receive():
        while True:
            try:
                data = await websocket.receive_text()
                print(data)
                await handle_message(websocket, clientID, data)
            except WebSocketDisconnect:
                break

    tasks_list = [
        asyncio.create_task(receive()),
    ]
    try:
        await asyncio.gather(*tasks_list)
    except WebSocketDisconnect:
        print(f"websocket {clientID} disconnected.")


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    uvicorn.run(
        app="aichat-server:app",
        host="localhost",
        port=4999,
        reload=False,
    )
