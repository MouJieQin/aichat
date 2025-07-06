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
from typing import Callable, Awaitable, Dict, Optional
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
API = OpenAIChatAPI(AI_CONFIG, DB)
speaker = Speaker(configure)
recognizer = Recognizer(configure)
spa_websockes: Dict[int, WebSocket] = {}
session_websockes: Dict[int, Dict[int, WebSocket]] = {}


def update_session_ai_config():
    sessions = API.get_all_session_id_title_config()
    # API.delete_session(35)
    for session in sessions:
        session_id = session[0]
        config = json.loads(session[2])

        if "top" not in config:
            config["top"] = False
        if "speech_rate" not in config:
            config["speech_rate"] = 1.0
        if "auto_play" not in config:
            config["auto_play"] = False
        if "tts_voice" not in config:
            config["tts_voice"] = "zh-CN-XiaochenNeural"
        if "auto_gen_title" not in config:
            config["auto_gen_title"] = True
        if "suggestions" not in config:
            config["suggestions"] = []
        if "last_active_time" not in config:
            config["last_active_time"] = time.time()
        API.update_session_ai_config(session_id, config)


update_session_ai_config()


async def broadcast_spa_websockes(msg: str):
    invalide_keys = []
    for key, websocket in spa_websockes.items():
        try:
            await websocket.send_text(msg)
        except Exception as e:
            logger.error(f"broadcast_spa_websockes error: {e}")
            invalide_keys.append(key)
    for key in invalide_keys:
        del spa_websockes[key]


async def broadcast_session_websockes(session_id: int, msg: str):
    # 确保 session_id 是整数类型
    session_id = int(session_id)
    if session_id not in session_websockes:
        return
    invalid_keys = []
    for key, websocket in session_websockes[session_id].items():
        try:
            await websocket.send_text(msg)
        except Exception as e:
            invalid_keys.append(key)
    # 移除无效的 WebSocket 连接
    for key in invalid_keys:
        del session_websockes[session_id][key]


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
    elif type == "copy_session":
        session_id = message["data"]["session_id"]
        new_session_id = API.copy_session(session_id)
        if new_session_id is None:
            raise ValueError("Session copy failed")
        title = API.get_session_title(session_id)
        config = API.get_session_ai_config(session_id)
        config["last_active_time"] = time.time()
        config["suggestions"] = []
        API.update_session_ai_config(new_session_id, config)
        msg = {
            "type": "new_session",
            "data": {
                "session_id": new_session_id,
                "title": title,
                "config": config,
            },
        }
        await websocket.send_text(json.dumps(msg))
    elif type == "copy_session_and_message":
        session_id = message["data"]["session_id"]
        new_session_id = API.copy_session_and_messages(session_id)
        if new_session_id is None:
            raise ValueError("Session copy failed")
        title = API.get_session_title(session_id)
        config = API.get_session_ai_config(session_id)
        config["last_active_time"] = time.time()
        API.update_session_ai_config(new_session_id, config)
        msg = {
            "type": "new_session",
            "data": {
                "session_id": new_session_id,
                "title": title,
                "config": config,
            },
        }
        await websocket.send_text(json.dumps(msg))
    elif type == "update_session_title":
        session_id = message["data"]["session_id"]
        title = message["data"]["title"]
        await update_session_title(session_id, title)
        API.update_session_ai_config_by_key(session_id, "auto_gen_title", False)
        await send_session_ai_config(session_id)
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
                    "title": title,
                    "system_prompt": system_prompt,
                    "config": config,
                },
            }
            await websocket.send_text(json.dumps(msg))


@app.websocket("/ws/aichat/spa")
async def websocketEndpointSpa(websocket: WebSocket):
    await websocket.accept()
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
                logger.info(f"websocket spa disconnected.")
                break

    tasks_list = [
        asyncio.create_task(receive()),
    ]
    try:
        await asyncio.gather(*tasks_list)
    except WebSocketDisconnect:
        logger.info(f"websocket spa disconnected.")
    except Exception as e:
        logger.error(f"websocket spa error: {e}")
    finally:
        del spa_websockes[time_id]


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
        try:
            await websocket.send_text(json.dumps(msg))
        except Exception as e:
            speaker.stop()
            logger.error(f"_create_play_sentence_callback error: {e}")

    return play_sentence_callback


async def _play_sentences(
    websocket: WebSocket,
    clientID: int,
    message_id: int,
    sentence_id_start: int,
    sentences: list,
    voice_name: str,
    speech_rate: float,
):
    play_sentence_callback = _create_play_sentence_callback(websocket, message_id)
    await play_sentence_callback(-2)

    def play_sentences():
        asyncio.run(
            speaker.play_sentences(
                str(clientID),
                str(message_id),
                str(sentence_id_start),
                sentences,
                play_sentence_callback,
                voice_name,
                speech_rate,
            )
        )

    threading.Thread(target=play_sentences, daemon=True).start()


async def handle_message(websocket: WebSocket, clientID: int, message_text: str):
    session_id = int(clientID)
    message = json.loads(message_text)
    type = message["type"]
    if type != "parsed_response":
        logger.info(f"receive message:{message}")
    if type == "user_input":
        user_message = message["data"]["user_message"]
        session_id = message["data"]["session_id"]
        auto_gen_title = message["data"]["auto_gen_title"]

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

        async def assistant_response_callback_async(
            response: str, is_streaming: bool, error: bool = False
        ):
            msg = {
                "type": "stream_response",
                "data": {
                    "is_streaming": is_streaming,
                    "is_chat_error": error,
                    "response": response,
                },
            }
            await websocket.send_text(json.dumps(msg))

        WITH_SYSTEM_PROMPT = True
        try:
            response_dict = await API.chat(
                WITH_SYSTEM_PROMPT,
                session_id,
                user_message,
                json.dumps({"sentences": []}),
                user_message_callback_async,
                assistant_response_callback_async,
            )
        except Exception as e:
            logger.error(f"Chat error: {e}")
            await assistant_response_callback_async(f"Chat error: {e}", True, True)
            return
        response = response_dict["response"]
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

        async def system_handle():
            system_info = {}
            if WITH_SYSTEM_PROMPT:
                system_info = response_dict
            else:
                # SQLite objects created in a thread can only be used in that same thread.
                system_prompt_content = API.get_session_system_message(session_id)
                system_ai_response = API.system_chat(
                    system_prompt_content, user_message, response
                )
                if system_ai_response is None:
                    return
                system_info = json.loads(system_ai_response)
            title = system_info["title"]
            suggestions = system_info["suggestions"]
            logger.info("title:%s, suggestions:%s", title, suggestions)
            if auto_gen_title:
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
        await send_session_ai_config(session_id)
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
    elif type == "generate_audio_files":
        session_id = message["data"]["session_id"]
        message_id = message["data"]["message_id"]
        sentence_id_start = message["data"]["sentence_id_start"]
        sentence_id_end = message["data"]["sentence_id_end"]
        ai_config = API.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]
        sentences = API.get_sentences(message_id)
        if sentences is None:
            logger.warning("message_id:{} not found any sentences".format(message_id))
            return
        threading.Thread(
            target=speaker.generate_audio_files,
            args=(
                session_id,
                message_id,
                sentence_id_start,
                sentence_id_end,
                sentences,
                voice_name,
                speech_rate,
            ),
            daemon=True,
        ).start()

    elif type == "play_the_sentence":
        message_id = message["data"]["message_id"]
        sentence_id = message["data"]["sentence_id"]
        ai_config = API.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]
        sentences = API.get_sentences(message_id)
        if sentences is None:
            logger.warning("message_id:{} not found any sentences".format(message_id))
            return
        logger.info("play_the_sentence:{}".format(sentences[sentence_id]["text"]))

        play_sentence_callback = _create_play_sentence_callback(websocket, message_id)
        await play_sentence_callback(-2)

        def play_sentence():
            asyncio.run(
                speaker.play_sentence(
                    str(clientID),
                    message_id,
                    sentence_id,
                    sentences,
                    play_sentence_callback,
                    voice_name,
                    speech_rate,
                )
            )

        threading.Thread(target=play_sentence, daemon=True).start()
    elif type == "play_sentences":
        message_id = message["data"]["message_id"]
        sentence_id_start = message["data"]["sentence_id"]
        sentences = API.get_sentences(message_id)
        ai_config = API.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]
        if sentences is None:
            logger.warning("message_id:{} not found any sentences".format(message_id))
            return
        await _play_sentences(
            websocket,
            clientID,
            message_id,
            sentence_id_start,
            sentences,
            voice_name,
            speech_rate,
        )
    elif type == "pause":
        speaker.pause()
    elif type == "play":
        if speaker.is_busy():
            speaker.unpause()
        else:
            message_id = message["data"]["message_id"]
            ai_config = API.get_session_ai_config(session_id)
            voice_name = ai_config["tts_voice"]
            speech_rate = ai_config["speech_rate"]
            sentence_id_start = 0
            sentences = API.get_sentences(message_id)
            if sentences is not None:
                await _play_sentences(
                    websocket,
                    clientID,
                    message_id,
                    sentence_id_start,
                    sentences,
                    voice_name,
                    speech_rate,
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


async def send_session_ai_config(
    session_id: int, websocket: Optional[WebSocket] = None
):
    ai_config = API.get_session_ai_config(session_id)
    msg = {
        "type": "session_ai_config",
        "data": {
            "ai_config": ai_config,
        },
    }
    if websocket is None:
        await broadcast_session_websockes(session_id, json.dumps(msg))
    else:
        await websocket.send_text(json.dumps(msg))


@app.websocket("/ws/aichat/{clientID}")
async def websocketEndpointAIchatSession(websocket: WebSocket, clientID: int):
    await websocket.accept()
    session_id = int(clientID)
    if not API.is_session_exist(session_id):
        msg = {"type": "error_session_not_exist", "data": {"session_id": session_id}}
        await websocket.send_text(json.dumps(msg))
        await websocket.close()
        return

    time_id = int(time.time() * 1000)
    if session_id not in session_websockes:
        session_websockes[session_id] = {}
    session_websockes[session_id][time_id] = websocket

    await send_session_messages(websocket, session_id)
    await send_session_ai_config(session_id, websocket)

    async def receive():
        while True:
            try:
                data = await websocket.receive_text()
                await handle_message(websocket, clientID, data)
            except WebSocketDisconnect:
                logger.info(f"websocket {clientID} disconnected.")
                break

    tasks_list = [
        asyncio.create_task(receive()),
    ]
    try:
        await asyncio.gather(*tasks_list)
    except WebSocketDisconnect:
        print(f"websocket {clientID} disconnected.")
    except Exception as e:
        logger.error(f"websocket {clientID} error: {e}")
    finally:
        del session_websockes[session_id][time_id]


if __name__ == "__main__":
    uvicorn.run(
        app="aichat-server:app",
        # host="0.0.0.0",
        host="localhost",
        port=4999,
        reload=False,
    )
