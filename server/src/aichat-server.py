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
from libs.openai_chat_api import OpenAIChatAPI
from libs.chat_database import ChatDatabase
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
AI_CONFIG = configure["ai_assistant"]
AI_CONFIG_DEFAULT = AI_CONFIG["default"]
DEFAULT_AI_CONFIG = AI_CONFIG[AI_CONFIG_DEFAULT["ai_config_name"]]
DB = ChatDatabase()
API = OpenAIChatAPI(DB, DEFAULT_AI_CONFIG["api_key"], DEFAULT_AI_CONFIG["base_url"])
database = {}
speaker = Speaker(configure)
id_counter = 1


async def send_all_sessions(websocket: WebSocket):
    sessions = API.get_all_session_id_title()
    print("sessions:{}".format(sessions))
    msg = {
        "type": "all_sessions",
        "data": sessions,
    }
    await websocket.send_text(json.dumps(msg))


async def handle_spa_message(websocket: WebSocket, message_text: str):
    message = json.loads(message_text)
    type = message["type"]
    if type == "get_all_sessions":
        await send_all_sessions(websocket)
    elif type == "create_session":
        system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
        parsed_system_prompt = json.dumps({"sentences": []})
        system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
        title = AI_CONFIG_DEFAULT["chat_title"]
        session_id, message_id = API.create_new_session(
            title, DEFAULT_AI_CONFIG, system_prompt, parsed_system_prompt
        )
        message = {
            "type": "parse_request",
            "data": {
                "type": "create_session",
                "data": {
                    "session_id": session_id,
                    "message_id": message_id,
                    "system_prompt": system_prompt,
                },
            },
        }
        await websocket.send_text(json.dumps(message))
    elif type == "parsed_response":
        parsed_type = message["data"]["type"]
        if parsed_type == "create_session":
            parsed_data = message["data"]["data"]
            message_id = parsed_data["message_id"]
            session_id = parsed_data["session_id"]
            title = AI_CONFIG_DEFAULT["chat_title"]
            system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
            parsed_text = {"sentences": parsed_data["sentences"]}
            API.update_message(message_id, parsed_text=json.dumps(parsed_text))
            msg = {
                "type": "new_session",
                "data": {
                    "session_id": session_id,
                    "message_id": message_id,
                    "title": title,
                    "system_prompt": system_prompt,
                    "ai_config": DEFAULT_AI_CONFIG,
                },
            }
            await websocket.send_text(json.dumps(msg))


@app.websocket("/ws/aichat/spa")
async def websocketEndpointSpa(websocket: WebSocket):
    await websocket.accept()
    await send_all_sessions(websocket)

    async def receive():
        while True:
            try:
                data = await websocket.receive_text()
                print(data)
                await handle_spa_message(websocket, data)
            except WebSocketDisconnect:
                break

    tasks_list = [
        asyncio.create_task(receive()),
    ]
    try:
        await asyncio.gather(*tasks_list)
    except WebSocketDisconnect:
        print(f"websocket spa disconnected.")


async def handle_message(websocket: WebSocket, clientID: int, message_text: str):
    message = json.loads(message_text)
    type = message["type"]
    print("receive message:", message)
    if type == "user_input":
        user_message = message["data"]["user_message"]
        session_id = message["data"]["session_id"]

        async def callback_async(message_id: int):
            msg = {
                "type": "parse_request",
                "data": {
                    "type": "user_message",
                    "data": {
                        "message_id": message_id,
                        "user_message": user_message,
                    },
                },
            }

            await websocket.send_text(json.dumps(msg))

        response = await API.chat(
            session_id, user_message, json.dumps({"sentences": []}), callback_async
        )
        message_id = API.add_assistant_message(
            session_id, response, json.dumps({"sentences": []})
        )
        msg = {
            "type": "parse_request",
            "data": {
                "type": "ai_response",
                "data": {"message_id": message_id, "response": response},
            },
        }
        await websocket.send_text(json.dumps(msg))
    elif type == "parsed_response":
        parsed_type = message["data"]["type"]
        if parsed_type == "user_message":
            message_id = message["data"]["data"]["message_id"]
            sentences = message["data"]["data"]["sentences"]
            API.update_message(
                message_id, json.dumps({"sentences": sentences}, ensure_ascii=False)
            )
            # database[clientID] = {}
            # database[clientID][message_id] = {}
            # database[clientID][message_id]["text"] = user_message
        elif parsed_type == "ai_response":
            message_id = message["data"]["data"]["message_id"]
            sentences = message["data"]["data"]["sentences"]
            API.update_message(
                message_id, json.dumps({"sentences": sentences}, ensure_ascii=False)
            )
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


async def send_session_messages(websocket: WebSocket, session_id: int):
    messages = API.get_session_messages(session_id, limit=100)
    print("messages:{}".format(messages))
    msg = {
        "type": "session_messages",
        "data": messages,
    }
    await websocket.send_text(json.dumps(msg))


@app.websocket("/ws/aichat/{clientID}")
async def websocketEndpointAIchatSession(websocket: WebSocket, clientID: int):
    await websocket.accept()
    await send_session_messages(websocket, int(clientID))

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
