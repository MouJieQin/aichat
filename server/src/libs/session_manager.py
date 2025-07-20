import json
import time
from typing import Optional
from fastapi import WebSocket
from libs.log_config import logger
from libs.common import Utils
from libs.openai_chat_api import OpenAIChatAPI


class SessionManager:
    """会话管理器，负责会话的创建、删除、配置更新等操作"""

    @staticmethod
    def initialize_sessions():
        """初始化会话配置"""

        def initialize_sessions_imple():
            sessions = Utils.api.get_all_session_id_title_config()
            for session in sessions:
                session_id = session["id"]
                config = json.loads(session["ai_config"])
                is_changed = False

                # 更新缺失的配置项
                for key, default_value in [
                    ("top", False),
                    ("speech_rate", 1.0),
                    ("auto_play", False),
                    ("tts_voice", "zh-CN-XiaochenNeural"),
                    ("auto_gen_title", True),
                    ("suggestions", []),
                    ("last_active_time", time.time()),
                    ("ai_avatar_url", ""),
                ]:
                    if key not in config:
                        config[key] = default_value
                        is_changed = True

                if is_changed:
                    Utils.api.update_session_ai_config(session_id, config)

        initialize_sessions_imple()

    @staticmethod
    async def broadcast_spa(message: str):
        """向所有SPA WebSocket连接广播消息"""
        invalid_keys = []
        for key, websocket in Utils.spa_websockets.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"SPA广播错误: {e}")
                invalid_keys.append(key)

        for key in invalid_keys:
            del Utils.spa_websockets[key]

    @staticmethod
    async def broadcast_session(session_id: int, message: str):
        """向特定会话的所有WebSocket连接广播消息"""
        session_id = int(session_id)
        if session_id not in Utils.session_websockets:
            return

        invalid_keys = []
        for key, websocket in Utils.session_websockets[session_id].items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"会话广播错误: {e}")
                invalid_keys.append(key)

        # 移除无效连接
        for key in invalid_keys:
            del Utils.session_websockets[session_id][key]

    @staticmethod
    async def broadcast_session_title(session_id: int, api: OpenAIChatAPI = Utils.api):
        """向特定会话的所有WebSocket连接广播标题"""
        title = api.get_session_title(session_id)
        msg = {
            "type": "session_title",
            "data": {
                "title": title,
            },
        }
        await SessionManager.broadcast_session(session_id, json.dumps(msg))

    @staticmethod
    async def update_title(session_id: int, title: str, api: OpenAIChatAPI = Utils.api):
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
        await SessionManager.broadcast_session_title(session_id, api)

    @staticmethod
    async def update_session_ai_avatar(session_id: int, ai_avatar_url: str):
        Utils.api.update_session_ai_avatar_url(session_id, ai_avatar_url)
        msg = {
            "type": "update_session_ai_avatar",
            "data": {
                "session_id": session_id,
                "ai_avatar_url": ai_avatar_url,
            },
        }
        await SessionManager.broadcast_spa(json.dumps(msg))
        await SessionManager.send_session_config(session_id)

    @staticmethod
    async def send_all_sessions(api: OpenAIChatAPI = Utils.api):
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
    async def send_system_config():
        """发送系统配置到SPA"""
        global CONFIG
        msg = {
            "type": "system_config",
            "data": {
                "system_config": Utils.CONFIG,
            },
        }
        print(msg)
        await SessionManager.broadcast_spa(json.dumps(msg))

    @staticmethod
    async def send_session_messages(websocket: WebSocket, session_id: int):
        """发送会话消息到指定WebSocket"""
        messages = Utils.api.get_session_messages(session_id, limit=-1)
        msg = {
            "type": "session_messages",
            "data": {"messages": messages},
        }
        await websocket.send_text(json.dumps(msg))

    @staticmethod
    async def send_session_config(
        session_id: int,
        websocket: Optional[WebSocket] = None,
        api: OpenAIChatAPI = Utils.api,
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
