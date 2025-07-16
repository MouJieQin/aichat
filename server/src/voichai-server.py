#!/usr/bin/env python3
# _*_coding:utf-8_*_

import json
import os
import time

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from libs.log_config import logger

from libs.config import spa_websockets, session_websockets, api
from libs.session_manager import SessionManager
from libs.message_handler import MessageHandler

# 配置应用
app = FastAPI(title="AI Chat Server", description="WebSocket-based AI chat server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        await SessionManager.broadcast_session_title(session_id)

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
    os.chdir(os.path.dirname(__file__))
    # 初始化会话
    SessionManager.initialize_sessions()

    # 启动服务器
    uvicorn.run(
        app="voichai-server:app",
        host="localhost",
        port=4999,
        reload=False,
    )
