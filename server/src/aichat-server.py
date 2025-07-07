#!/usr/bin/env python3
# _*_coding:utf-8_*_
import json
import os
import time
import threading
import asyncio
import signal
from typing import Dict, Optional, Callable, Awaitable, List
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Path as APIPath,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import netifaces
import plistlib
from pathvalidate import is_valid_filename, sanitize_filename
import appdirs
from send2trash import send2trash

from libs.speaker import Speaker
from libs.openai_chat_api import OpenAIChatAPI
from libs.chat_database import ChatDatabase
from libs.recognizer import Recognizer
from libs.log_config import logger

# 配置应用
app = FastAPI(title="AI Chat Server", description="WebSocket-based AI chat server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载配置
config_file = Path("./configure.json")
with open(config_file, "r") as f:
    CONFIG = json.load(f)

AI_CONFIG = CONFIG["ai_assistant"]
AI_CONFIG_DEFAULT = AI_CONFIG["default"]
DEFAULT_AI_CONFIG = AI_CONFIG[AI_CONFIG_DEFAULT["ai_config_name"]]

# 初始化服务
db = ChatDatabase()
api = OpenAIChatAPI(AI_CONFIG, db)
speaker = Speaker(CONFIG)
recognizer = Recognizer(CONFIG)

# WebSocket 连接管理
spa_websockets: Dict[int, WebSocket] = {}
session_websockets: Dict[int, Dict[int, WebSocket]] = {}


class SessionManager:
    """会话管理器，负责会话的创建、删除、配置更新等操作"""

    @staticmethod
    def initialize_sessions():
        """初始化会话配置"""
        sessions = api.get_all_session_id_title_config()
        for session in sessions:
            session_id = session["id"]
            config = json.loads(session["ai_config"])

            # 更新缺失的配置项
            for key, default_value in [
                ("top", False),
                ("speech_rate", 1.0),
                ("auto_play", False),
                ("tts_voice", "zh-CN-XiaochenNeural"),
                ("auto_gen_title", True),
                ("suggestions", []),
                ("last_active_time", time.time()),
            ]:
                if key not in config:
                    config[key] = default_value

            api.update_session_ai_config(session_id, config)

    @staticmethod
    async def broadcast_spa(message: str):
        """向所有SPA WebSocket连接广播消息"""
        invalid_keys = []
        for key, websocket in spa_websockets.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"SPA广播错误: {e}")
                invalid_keys.append(key)

        for key in invalid_keys:
            del spa_websockets[key]

    @staticmethod
    async def broadcast_session(session_id: int, message: str):
        """向特定会话的所有WebSocket连接广播消息"""
        session_id = int(session_id)
        if session_id not in session_websockets:
            return

        invalid_keys = []
        for key, websocket in session_websockets[session_id].items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"会话广播错误: {e}")
                invalid_keys.append(key)

        # 移除无效连接
        for key in invalid_keys:
            del session_websockets[session_id][key]

    @staticmethod
    async def update_title(session_id: int, title: str):
        """更新会话标题并广播"""
        api.update_session_title(session_id, title)
        msg = {
            "type": "update_session_title",
            "data": {
                "session_id": session_id,
                "title": title,
            },
        }
        await SessionManager.broadcast_spa(json.dumps(msg))

    @staticmethod
    async def send_all_sessions():
        """发送所有会话信息到SPA"""
        sessions = api.get_all_session_id_title_config()
        msg = {
            "type": "all_sessions",
            "data": {
                "sessions": sessions,
            },
        }
        await SessionManager.broadcast_spa(json.dumps(msg))

    @staticmethod
    async def send_session_messages(websocket: WebSocket, session_id: int):
        """发送会话消息到指定WebSocket"""
        messages = api.get_session_messages(session_id, limit=-1)
        msg = {
            "type": "session_messages",
            "data": {"messages": messages},
        }
        await websocket.send_text(json.dumps(msg))

    @staticmethod
    async def send_session_config(
        session_id: int, websocket: Optional[WebSocket] = None
    ):
        """发送会话配置到指定WebSocket或广播"""
        ai_config = api.get_session_ai_config(session_id)
        msg = {
            "type": "session_ai_config",
            "data": {
                "ai_config": ai_config,
            },
        }

        if websocket:
            await websocket.send_text(json.dumps(msg))
        else:
            await SessionManager.broadcast_session(session_id, json.dumps(msg))


class MessageHandler:
    """消息处理器，处理不同类型的WebSocket消息"""

    @staticmethod
    async def handle_spa_message(websocket: WebSocket, message_text: str):
        """处理SPA WebSocket消息"""
        try:
            message = json.loads(message_text)
            message_type = message["type"]
            if message_type != "parsed_response":
                logger.info(f"接收消息: {message}")

            handlers = {
                "get_all_sessions": MessageHandler._handle_get_all_sessions,
                "create_session": MessageHandler._handle_create_session,
                "copy_session": MessageHandler._handle_copy_session,
                "copy_session_and_message": MessageHandler._handle_copy_session_and_message,
                "update_session_title": MessageHandler._handle_update_session_title,
                "delete_session": MessageHandler._handle_delete_session,
                "update_session_top": MessageHandler._handle_update_session_top,
                "parsed_response": MessageHandler._handle_parsed_response,
            }

            if message_type in handlers:
                await handlers[message_type](websocket, message)
            else:
                logger.warning(f"未知的SPA消息类型: {message_type}")

        except Exception as e:
            logger.error(f"处理SPA消息时出错: {e}")

    @staticmethod
    async def _handle_get_all_sessions(websocket: WebSocket, message: dict):
        await SessionManager.send_all_sessions()

    @staticmethod
    async def _handle_create_session(websocket: WebSocket, message: dict):
        system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
        parsed_system_prompt = json.dumps({"sentences": []})
        title = AI_CONFIG_DEFAULT["chat_title"]

        config = json.loads(json.dumps(DEFAULT_AI_CONFIG))
        config["top"] = False
        config["last_active_time"] = time.time()
        config["suggestions"] = []

        session_id, message_id = api.create_new_session(
            title, config, system_prompt, parsed_system_prompt
        )

        response = {
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
        await websocket.send_text(json.dumps(response))

    @staticmethod
    async def _handle_copy_session(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        new_session_id = api.copy_session(session_id)

        if new_session_id is None:
            raise ValueError("会话复制失败")

        title = api.get_session_title(session_id)
        config = api.get_session_ai_config(session_id)
        config["last_active_time"] = time.time()
        config["suggestions"] = []
        api.update_session_ai_config(new_session_id, config)

        msg = {
            "type": "new_session",
            "data": {
                "session_id": new_session_id,
                "title": title,
                "config": config,
            },
        }
        await websocket.send_text(json.dumps(msg))

    @staticmethod
    async def _handle_copy_session_and_message(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        new_session_id = api.copy_session_and_messages(session_id)

        if new_session_id is None:
            raise ValueError("会话复制失败")

        title = api.get_session_title(session_id)
        config = api.get_session_ai_config(session_id)
        config["last_active_time"] = time.time()
        api.update_session_ai_config(new_session_id, config)

        msg = {
            "type": "new_session",
            "data": {
                "session_id": new_session_id,
                "title": title,
                "config": config,
            },
        }
        await websocket.send_text(json.dumps(msg))

    @staticmethod
    async def _handle_update_session_title(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        title = message["data"]["title"]

        await SessionManager.update_title(session_id, title)
        api.update_session_property(session_id, "auto_gen_title", False)
        await SessionManager.send_session_config(session_id)

    @staticmethod
    async def _handle_delete_session(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        api.delete_session(session_id)

        msg = {
            "type": "delete_session",
            "data": {
                "session_id": session_id,
            },
        }
        await websocket.send_text(json.dumps(msg))

    @staticmethod
    async def _handle_update_session_top(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        top = message["data"]["top"]

        api.update_session_top(session_id, top)

        msg = {
            "type": "update_session_top",
            "data": {
                "session_id": session_id,
                "top": top,
            },
        }
        await SessionManager.broadcast_spa(json.dumps(msg))

    @staticmethod
    async def _handle_parsed_response(websocket: WebSocket, message: dict):
        parsed_type = message["data"]["type"]

        if parsed_type == "create_session":
            parsed_data = message["data"]["data"]
            message_id = parsed_data["message_id"]
            session_id = parsed_data["session_id"]
            config = api.get_session_ai_config(session_id)

            title = AI_CONFIG_DEFAULT["chat_title"]
            system_prompt = AI_CONFIG_DEFAULT["system_prompt"]
            parsed_text = {"sentences": parsed_data["sentences"]}

            api.update_message(message_id, parsed_text=json.dumps(parsed_text))

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

    @staticmethod
    async def handle_session_message(
        websocket: WebSocket, client_id: int, message_text: str
    ):
        """处理会话WebSocket消息"""
        try:
            session_id = int(client_id)
            message = json.loads(message_text)
            message_type = message["type"]

            if message_type != "parsed_response":
                logger.info(f"接收消息: {message}")

            handlers = {
                "user_input": MessageHandler._handle_user_input,
                "parsed_response": MessageHandler._handle_session_parsed_response,
                "update_session_ai_config": MessageHandler._handle_update_session_config,
                "update_message": MessageHandler._handle_update_message,
                "delete_audio_files": MessageHandler._handle_delete_audio_files,
                "delete_message": MessageHandler._handle_delete_message,
                "start_speech_recognize": MessageHandler._handle_start_speech_recognize,
                "update_cursor_position": MessageHandler._handle_update_cursor_position,
                "stop_speech_recognize": MessageHandler._handle_stop_speech_recognize,
                "generate_audio_files": MessageHandler._handle_generate_audio_files,
                "play_the_sentence": MessageHandler._handle_play_the_sentence,
                "play_sentences": MessageHandler._handle_play_sentences,
                "pause": MessageHandler._handle_pause,
                "play": MessageHandler._handle_play,
                "stop": MessageHandler._handle_stop,
            }

            if message_type in handlers:
                await handlers[message_type](websocket, session_id, message)
            else:
                logger.warning(f"未知的会话消息类型: {message_type}")

        except Exception as e:
            logger.error(f"处理会话消息时出错: {e}")

    @staticmethod
    async def _handle_user_input(websocket: WebSocket, session_id: int, message: dict):
        user_message = message["data"]["user_message"]
        auto_gen_title = message["data"]["auto_gen_title"]

        async def user_message_callback(message_id: int):
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

        async def assistant_response_callback(
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
            response_dict = await api.chat(
                WITH_SYSTEM_PROMPT,
                session_id,
                user_message,
                json.dumps({"sentences": []}),
                user_message_callback,
                assistant_response_callback,
            )
        except Exception as e:
            logger.error(f"聊天错误: {e}")
            await assistant_response_callback(f"聊天错误: {e}", True, True)
            return

        response = response_dict["response"]
        message_id = api.add_assistant_message(
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
                system_prompt_content = api.get_session_system_message(session_id)
                system_ai_response = api.system_chat(
                    system_prompt_content, user_message, response
                )
                if system_ai_response is None:
                    return
                system_info = json.loads(system_ai_response)

            title = system_info["title"]
            suggestions = system_info["suggestions"]
            logger.info("标题:%s, 建议:%s", title, suggestions)

            if auto_gen_title:
                await SessionManager.update_title(session_id, title)

            msg = {
                "type": "session_suggestions",
                "data": {
                    "session_id": session_id,
                    "suggestions": suggestions,
                },
            }
            await websocket.send_text(json.dumps(msg))

            config = api.get_session_ai_config(session_id)
            config["last_active_time"] = time.time()
            config["suggestions"] = suggestions
            api.update_session_ai_config(session_id, config)
            await SessionManager.send_all_sessions()

        await system_handle()

    @staticmethod
    async def _handle_session_parsed_response(
        websocket: WebSocket, session_id: int, message: dict
    ):
        parsed_type = message["data"]["type"]

        if parsed_type == "user_message":
            message_id = message["data"]["data"]["message_id"]
            sentences = message["data"]["data"]["sentences"]
            api.update_message(
                message_id, json.dumps({"sentences": sentences}, ensure_ascii=False)
            )
        elif parsed_type == "ai_response":
            message_id = message["data"]["data"]["message_id"]
            sentences = message["data"]["data"]["sentences"]
            api.update_message(
                message_id, json.dumps({"sentences": sentences}, ensure_ascii=False)
            )

    @staticmethod
    async def _handle_update_session_config(
        websocket: WebSocket, session_id: int, message: dict
    ):
        ai_config = message["data"]["ai_config"]
        api.update_session_ai_config(session_id, ai_config)
        await SessionManager.send_session_config(session_id)

    @staticmethod
    async def _handle_update_message(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        raw_text = message["data"]["raw_text"]
        sentences = message["data"]["sentences"]

        speaker.remove_audio_directory(session_id, message_id)
        parsed_text = {"sentences": sentences}

        api.update_message(
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

    @staticmethod
    async def _handle_delete_audio_files(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        speaker.remove_audio_directory(session_id, message_id)

    @staticmethod
    async def _handle_delete_message(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]

        api.delete_message(message_id)
        speaker.remove_audio_directory(session_id, message_id)

        msg = {
            "type": "delete_message",
            "data": {
                "message_id": message_id,
            },
        }
        await websocket.send_text(json.dumps(msg))

    @staticmethod
    async def _handle_start_speech_recognize(
        websocket: WebSocket, session_id: int, message: dict
    ):
        language = message["data"]["language"]
        input_text = message["data"]["input_text"]
        cursor_position = message["data"]["cursor_position"]

        await recognizer.start_recognition(
            websocket, language, input_text, cursor_position
        )

    @staticmethod
    async def _handle_update_cursor_position(
        websocket: WebSocket, session_id: int, message: dict
    ):
        original_text = message["data"]["original_text"]
        cursor_position = message["data"]["cursor_position"]
        recognizer.reset_text_state(original_text, cursor_position)

    @staticmethod
    async def _handle_stop_speech_recognize(
        websocket: WebSocket, session_id: int, message: dict
    ):
        await recognizer.stop_recognition()

    @staticmethod
    async def _handle_generate_audio_files(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        sentence_id_start = message["data"]["sentence_id_start"]
        sentence_id_end = message["data"]["sentence_id_end"]

        ai_config = api.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]

        sentences = api.get_sentences(message_id)
        if sentences is None:
            logger.warning(f"消息ID:{message_id} 未找到句子")
            return

        threading.Thread(
            target=speaker.pregenerate_audio_files,
            args=(
                session_id,
                message_id,
                sentences[sentence_id_start : sentence_id_end + 1],
                voice_name,
                speech_rate,
            ),
            daemon=True,
        ).start()

    @staticmethod
    async def _handle_play_the_sentence(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        sentence_id = message["data"]["sentence_id"]

        ai_config = api.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]

        sentences = api.get_sentences(message_id)
        if sentences is None:
            logger.warning(f"消息ID:{message_id} 未找到句子")
            return

        logger.info(f"播放句子:{sentences[sentence_id]['text']}")

        async def play_sentence_callback(sentence_id: int):
            msg = {
                "type": "the_sentence_playing",
                "data": {
                    "message_id": message_id,
                    "sentence_id": sentence_id,
                },
            }
            try:
                await websocket.send_text(json.dumps(msg))
            except Exception as e:
                speaker.stop_playback()
                logger.error(f"播放回调错误: {e}")

        await play_sentence_callback(-2)

        def play_sentence():
            asyncio.run(
                speaker.play_sentence(
                    session_id,
                    message_id,
                    sentence_id,
                    sentences,
                    play_sentence_callback,
                    voice_name,
                    speech_rate,
                )
            )

        threading.Thread(target=play_sentence, daemon=True).start()

    @staticmethod
    async def _handle_play_sentences(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        sentence_id_start = message["data"]["sentence_id"]

        ai_config = api.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]

        sentences = api.get_sentences(message_id)
        if sentences is None:
            logger.warning(f"消息ID:{message_id} 未找到句子")
            return

        await MessageHandler._play_sentences_impl(
            websocket,
            session_id,
            message_id,
            sentence_id_start,
            sentences,
            voice_name,
            speech_rate,
        )

    @staticmethod
    async def _handle_pause(websocket: WebSocket, session_id: int, message: dict):
        speaker.pause_playback()

    @staticmethod
    async def _handle_unpause(websocket: WebSocket, session_id: int, message: dict):
        speaker.resume_playback()

    @staticmethod
    async def _handle_play(websocket: WebSocket, session_id: int, message: dict):
        if speaker.is_playing():
            speaker.resume_playback()
        else:
            message_id = message["data"]["message_id"]

            ai_config = api.get_session_ai_config(session_id)
            voice_name = ai_config["tts_voice"]
            speech_rate = ai_config["speech_rate"]
            sentence_id_start = 0

            sentences = api.get_sentences(message_id)
            if sentences is not None:
                await MessageHandler._play_sentences_impl(
                    websocket,
                    session_id,
                    message_id,
                    sentence_id_start,
                    sentences,
                    voice_name,
                    speech_rate,
                )

    @staticmethod
    async def _handle_stop(websocket: WebSocket, session_id: int, message: dict):
        speaker.stop_playback()

    @staticmethod
    async def _play_sentences_impl(
        websocket: WebSocket,
        session_id: int,
        message_id: int,
        sentence_id_start: int,
        sentences: list,
        voice_name: str,
        speech_rate: float,
    ):
        async def play_sentence_callback(sentence_id: int):
            msg = {
                "type": "the_sentence_playing",
                "data": {
                    "message_id": message_id,
                    "sentence_id": sentence_id,
                },
            }
            try:
                await websocket.send_text(json.dumps(msg))
            except Exception as e:
                speaker.stop_playback()
                logger.error(f"播放回调错误: {e}")

        await play_sentence_callback(-2)

        def play_sentences():
            asyncio.run(
                speaker.play_sentences(
                    session_id,
                    message_id,
                    sentence_id_start,
                    sentences,
                    play_sentence_callback,
                    voice_name,
                    speech_rate,
                )
            )

        threading.Thread(target=play_sentences, daemon=True).start()


# WebSocket 端点
@app.websocket("/ws/aichat/spa")
async def spa_websocket_endpoint(websocket: WebSocket):
    """SPA WebSocket端点"""
    await websocket.accept()
    connection_id = int(time.time() * 1000)
    spa_websockets[connection_id] = websocket

    try:
        await SessionManager.send_all_sessions()

        while True:
            data = await websocket.receive_text()
            await MessageHandler.handle_spa_message(websocket, data)

    except WebSocketDisconnect:
        logger.info(f"SPA WebSocket断开连接")
    except Exception as e:
        logger.error(f"SPA WebSocket错误: {e}")
    finally:
        if connection_id in spa_websockets:
            del spa_websockets[connection_id]


@app.websocket("/ws/aichat/{clientID}")
async def session_websocket_endpoint(websocket: WebSocket, clientID: int):
    """会话WebSocket端点"""
    await websocket.accept()

    session_id = int(clientID)
    if not api.is_session_exist(session_id):
        msg = {"type": "error_session_not_exist", "data": {"session_id": session_id}}
        await websocket.send_text(json.dumps(msg))
        await websocket.close()
        return

    connection_id = int(time.time() * 1000)

    if session_id not in session_websockets:
        session_websockets[session_id] = {}

    session_websockets[session_id][connection_id] = websocket

    try:
        await SessionManager.send_session_messages(websocket, session_id)
        await SessionManager.send_session_config(session_id, websocket)

        while True:
            data = await websocket.receive_text()
            await MessageHandler.handle_session_message(websocket, clientID, data)

    except WebSocketDisconnect:
        logger.info(f"会话WebSocket {clientID} 断开连接")
    except Exception as e:
        logger.error(f"会话WebSocket {clientID} 错误: {e}")
    finally:
        if (
            session_id in session_websockets
            and connection_id in session_websockets[session_id]
        ):
            del session_websockets[session_id][connection_id]


# 启动应用
if __name__ == "__main__":
    # 初始化会话
    SessionManager.initialize_sessions()

    # 启动服务器
    uvicorn.run(
        app="aichat-server:app",
        host="localhost",
        port=4999,
        reload=False,
    )
