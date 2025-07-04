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
from typing import Callable, Awaitable, Dict
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
from libs.recognizer import Recognizer
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
API = OpenAIChatAPI(
    AI_CONFIG, DB, DEFAULT_AI_CONFIG["api_key"], DEFAULT_AI_CONFIG["base_url"]
)
speaker = Speaker(configure)
recognizer = Recognizer(configure)
spa_websockes: Dict[int, WebSocket] = {}


def update_session_ai_config():
    sessions = API.get_all_session_id_title_config()
    # API.delete_session(35)
    # for session in sessions:
    #     session_id = session[0]
    #     config = json.loads(session[2])
    #     if "top" not in config:
    #         config["top"] = False
    #     if "suggestions" not in config:
    #         config["suggestions"] = []
    #     if "last_active_time" not in config:
    #         config["last_active_time"] = time.time()
    #     API.update_session_ai_config(session_id, config)


update_session_ai_config()


async def broadcast_spa_websockes(msg: str):
    in_valide_keys = []
    for key, websocket in spa_websockes.items():
        try:
            await websocket.send_text(msg)
        except Exception as e:
            logger.error(f"broadcast_spa_websockes error: {e}")
            in_valide_keys.append(key)
    for key in in_valide_keys:
        del spa_websockes[key]


async def update_session_title(session_id: int, title: str):
    API.update_session_title(session_id, title)
    msg = {
        "type": "update_session_title",
        "data": {
            "session_id": session_id,
            "title": title,
        },
    }
    await broadcast_spa_websockes(json.dumps(msg))


async def send_all_sessions():
    sessions = API.get_all_session_id_title_config()
    msg = {
        "type": "all_sessions",
        "data": {
            "sessions": sessions,
        },
    }
    await broadcast_spa_websockes(json.dumps(msg))


async def handle_spa_message(websocket: WebSocket, message_text: str):
    message = json.loads(message_text)
    type = message["type"]
    if type == "get_all_sessions":
        await send_all_sessions()
    elif type == "create_session":
        system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
        parsed_system_prompt = json.dumps({"sentences": []})
        system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
        title = AI_CONFIG_DEFAULT["chat_title"]

        config = json.loads(json.dumps(DEFAULT_AI_CONFIG))
        config["top"] = False
        config["last_active_time"] = time.time()
        config["suggestions"] = []
        session_id, message_id = API.create_new_session(
            title, config, system_prompt, parsed_system_prompt
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
    elif type == "update_session_title":
        session_id = message["data"]["session_id"]
        title = message["data"]["title"]
        await update_session_title(session_id, title)
    elif type == "delete_session":
        session_id = message["data"]["session_id"]
        API.delete_session(session_id)
        msg = {
            "type": "delete_session",
            "data": {
                "session_id": session_id,
            },
        }
        await websocket.send_text(json.dumps(msg))
    elif type == "update_session_top":
        session_id = message["data"]["session_id"]
        top = message["data"]["top"]
        API.update_session_top(session_id, top)
        msg = {
            "type": "update_session_top",
            "data": {
                "session_id": session_id,
                "top": top,
            },
        }
        await broadcast_spa_websockes(json.dumps(msg))
    elif type == "parsed_response":
        parsed_type = message["data"]["type"]
        if parsed_type == "create_session":
            parsed_data = message["data"]["data"]
            message_id = parsed_data["message_id"]
            session_id = parsed_data["session_id"]
            config = API.get_session_ai_config(session_id)

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
                    "config": config,
                },
            }
            await websocket.send_text(json.dumps(msg))


@app.websocket("/ws/aichat/spa")
async def websocketEndpointSpa(websocket: WebSocket):
    await websocket.accept()
    #  timestamp that's exact to the millisecond
    time_id = int(time.time() * 1000)
    spa_websockes[time_id] = websocket
    await send_all_sessions()

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
        spa_websockes.pop(time_id)
        logger.info(f"websocket spa disconnected.")


def _create_play_sentence_callback(
    websocket: WebSocket, message_id: int
) -> Callable[[int], Awaitable[None]]:
    async def play_sentence_callback(sentence_id: int):
        msg = {
            "type": "the_sentence_playing",
            "data": {
                "message_id": message_id,
                "sentence_id": sentence_id,
            },
        }
        print("the_sentence_playing:", msg)
        await websocket.send_text(json.dumps(msg))

    return play_sentence_callback


def _play_sentences(
    websocket: WebSocket,
    clientID: int,
    message_id: int,
    sentence_id_start: int,
    sentences: list,
    voice_name: str,
):
    play_sentence_callback = _create_play_sentence_callback(websocket, message_id)

    def play_sentences():
        asyncio.run(
            speaker.play_sentences(
                str(clientID),
                str(message_id),
                str(sentence_id_start),
                sentences,
                play_sentence_callback,
                voice_name,
            )
        )

    threading.Thread(target=play_sentences, daemon=True).start()


async def handle_message(websocket: WebSocket, clientID: int, message_text: str):
    message = json.loads(message_text)
    type = message["type"]
    print("receive message:", message)
    if type == "user_input":
        user_message = message["data"]["user_message"]
        session_id = message["data"]["session_id"]

        async def user_message_callback_async(message_id: int):
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

        async def assistant_response_callback_async(response: str, is_streaming: bool):
            msg = {
                "type": "stream_response",
                "data": {
                    "is_streaming": is_streaming,
                    "response": response,
                },
            }
            await websocket.send_text(json.dumps(msg))

        response = await API.chat(
            session_id,
            user_message,
            json.dumps({"sentences": []}),
            user_message_callback_async,
            assistant_response_callback_async,
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

        if response is None:
            return

        # SQLite objects created in a thread can only be used in that same thread.
        system_prompt_content = API.get_session_system_message(session_id)

        async def system_handle():
            system_ai_response = API.system_chat(
                system_prompt_content, user_message, response
            )
            if system_ai_response is None:
                return
            system_info = json.loads(system_ai_response)
            title = system_info["title"]
            suggestions = system_info["suggestions"]
            logger.info("title:%s, suggestions:%s", title, suggestions)
            await update_session_title(session_id, title)
            msg = {
                "type": "session_suggestions",
                "data": {
                    "session_id": session_id,
                    "suggestions": suggestions,
                },
            }
            await websocket.send_text(json.dumps(msg))

            config = API.get_session_ai_config(session_id)
            config["last_active_time"] = time.time()
            config["suggestions"] = suggestions
            API.update_session_ai_config(session_id, config)
            await send_all_sessions()

        await system_handle()

    elif type == "parsed_response":
        parsed_type = message["data"]["type"]
        if parsed_type == "user_message":
            message_id = message["data"]["data"]["message_id"]
            sentences = message["data"]["data"]["sentences"]
            API.update_message(
                message_id, json.dumps({"sentences": sentences}, ensure_ascii=False)
            )
        elif parsed_type == "ai_response":
            message_id = message["data"]["data"]["message_id"]
            sentences = message["data"]["data"]["sentences"]
            API.update_message(
                message_id, json.dumps({"sentences": sentences}, ensure_ascii=False)
            )
    elif type == "update_session_ai_config":
        session_id = message["data"]["session_id"]
        ai_config = message["data"]["ai_config"]
        API.update_session_ai_config(session_id, ai_config)
        await send_session_ai_config(websocket, session_id)
    elif type == "update_message":
        session_id = message["data"]["session_id"]
        message_id = message["data"]["message_id"]
        raw_text = message["data"]["raw_text"]
        sentences = message["data"]["sentences"]
        speaker.remove_audio_dir(session_id, message_id)
        parsed_text = {"sentences": sentences}
        API.update_message(
            message_id, raw_text=raw_text, parsed_text=json.dumps(parsed_text)
        )
        msg = {
            "type": "update_message",
            "data": {
                "message_id": message_id,
                "raw_text": raw_text,
            },
        }
        await websocket.send_text(json.dumps(msg))
    elif type == "delete_audio_files":
        message_id = message["data"]["message_id"]
        session_id = message["data"]["session_id"]
        speaker.remove_audio_dir(session_id, message_id)
    elif type == "delete_message":
        message_id = message["data"]["message_id"]
        session_id = message["data"]["session_id"]
        API.delete_message(message_id)
        speaker.remove_audio_dir(session_id, message_id)
        msg = {
            "type": "delete_message",
            "data": {
                "message_id": message_id,
            },
        }
        await websocket.send_text(json.dumps(msg))
    elif type == "start_speech_recognize":
        language = message["data"]["language"]
        input_text = message["data"]["input_text"]
        cursor_position = message["data"]["cursor_position"]
        recognizer.start_recognizer(websocket, language, input_text, cursor_position)
    elif type == "stop_speech_recognize":
        recognizer.stop_recognizer_sync()
    elif type == "play_the_sentence":
        message_id = message["data"]["message_id"]
        sentence_id = message["data"]["sentence_id"]
        voice_name = message["data"]["voice_name"]
        sentences = API.get_sentences(message_id)
        if sentences is None:
            logger.warning("message_id:{} not found any sentences".format(message_id))
            return
        logger.info("play_the_sentence:{}".format(sentences[sentence_id]["text"]))

        play_sentence_callback = _create_play_sentence_callback(websocket, message_id)

        def play_sentence():
            asyncio.run(
                speaker.play_sentence(
                    str(clientID),
                    message_id,
                    sentence_id,
                    sentences,
                    play_sentence_callback,
                    voice_name,
                )
            )

        threading.Thread(target=play_sentence, daemon=True).start()
    elif type == "play_sentences":
        message_id = message["data"]["message_id"]
        sentence_id_start = message["data"]["sentence_id"]
        sentences = API.get_sentences(message_id)
        voice_name = message["data"]["voice_name"]
        if sentences is None:
            logger.warning("message_id:{} not found any sentences".format(message_id))
            return
        _play_sentences(
            websocket, clientID, message_id, sentence_id_start, sentences, voice_name
        )
    elif type == "pause":
        speaker.pause()
    elif type == "play":
        if speaker.is_busy():
            speaker.unpause()
        else:
            message_id = message["data"]["message_id"]
            voice_name = message["data"]["voice_name"]
            sentence_id_start = 0
            sentences = API.get_sentences(message_id)
            if sentences is not None:
                _play_sentences(
                    websocket,
                    clientID,
                    message_id,
                    sentence_id_start,
                    sentences,
                    voice_name,
                )
    elif type == "stop":
        speaker.stop()


async def send_session_messages(websocket: WebSocket, session_id: int):
    messages = API.get_session_messages(session_id, limit=100)
    msg = {
        "type": "session_messages",
        "data": messages,
    }
    await websocket.send_text(json.dumps(msg))


async def send_session_ai_config(websocket: WebSocket, session_id: int):
    ai_config = API.get_session_ai_config(session_id)
    msg = {
        "type": "session_ai_config",
        "data": {
            "ai_config": ai_config,
        },
    }
    await websocket.send_text(json.dumps(msg))


@app.websocket("/ws/aichat/{clientID}")
async def websocketEndpointAIchatSession(websocket: WebSocket, clientID: int):
    await websocket.accept()
    await send_session_messages(websocket, int(clientID))
    await send_session_ai_config(websocket, int(clientID))

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
        # host="0.0.0.0",
        host="localhost",
        port=4999,
        reload=False,
    )
