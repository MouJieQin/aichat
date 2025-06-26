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
import threading
from libs.speaker import Speaker
from libs.log_config import logger

os.chdir(os.path.dirname(__file__))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

configure_file = Path("./configure.json")
with open(configure_file, "r") as f:
    configure = json.load(f)
database = {}
speaker = Speaker(configure)
id_counter = 1


async def handle_message(websocket: WebSocket, clientID: int, message_text: str):
    global id_counter
    message = json.loads(message_text)
    type = message["type"]
    if type == "user_input":
        text = message["data"]["text"]
        text_id = message["data"]["text_id"]
        database[clientID] = {}
        database[clientID][text_id] = {}
        database[clientID][text_id]["text"] = text
        message = {
            "type": "ai_response",
            "data": {"text_id": text_id + 1, "response": text},
        }
        print(message)
        database[clientID][text_id + 1] = {}
        database[clientID][text_id + 1]["text"] = text
        await websocket.send_text(json.dumps(message))
    elif type == "sentences":
        text_id = message["data"]["text_id"]
        sentences = message["data"]["sentences"]
        database[clientID][text_id]["sentences"] = sentences
        print(sentences)
    elif type == "click_sentence":
        text_id = message["data"]["text_id"]
        sentence_id = message["data"]["sentence_id"]

        print(database[clientID][text_id]["sentences"][sentence_id]["text"])

        def play_sentence():
            asyncio.run(
                speaker.play_sentence(
                    str(clientID),
                    text_id,
                    sentence_id,
                    database[clientID][text_id]["sentences"],
                )
            )

        threading.Thread(target=play_sentence, daemon=True).start()
    elif type == "play_sentences":
        text_id = message["data"]["text_id"]
        sentence_id_start = message["data"]["sentence_id"]
        sentences = database[clientID][text_id]["sentences"]

        def play_sentences():
            asyncio.run(
                speaker.play_sentences(
                    str(clientID),
                    text_id,
                    sentence_id_start,
                    sentences,
                )
            )

        threading.Thread(target=play_sentences, daemon=True).start()
    elif type == "pause":
        speaker.pause()
    elif type == "unpause":
        speaker.unpause()
    elif type == "stop":
        speaker.stop()


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
    uvicorn.run(
        app="aichat-server:app",
        host="localhost",
        port=4999,
        reload=False,
    )
