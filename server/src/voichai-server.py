#!/usr/bin/env python3
# _*_coding:utf-8_*_

import json
import os
import time
import asyncio

from fastapi import (
    FastAPI,
    UploadFile,
    Form,
    File,
    Path,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from starlette.responses import FileResponse
from pathlib import Path

from libs.log_config import logger
from libs.common import Utils
from libs.websocket_client import WsClient
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

# ==============================================
# WebSocket Client 连接 iWin 服务器
# ==============================================
# 全局单例（整个程序共用一个连接）
Utils.iwin_ws_client = WsClient(
    "ws://localhost:9999/ws/voichai", MessageHandler.handle_iwin_message
)


@app.get("/api/connectiwin")
async def connectiwin():
    if Utils.iwin_ws_client.is_connected():
        return {"status": "connected"}
    # 🔥 关键：用 create_task 后台启动，不阻塞接口
    asyncio.create_task(Utils.iwin_ws_client.connect())
    return {"status": "connecting"}



@app.get("/api/download")
async def download(path: str):
    logger.info(f"download path: {path}")
    path = Utils.DATA_PATH + path
    if not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="Not a file or does not exist")

    fr = FileResponse(
        path=path,
        filename=Path(path).name,
    )
    return fr


# 响应模型
class UploadResponse(BaseModel):
    success: bool
    file_url: str


# 单文件上传接口
@app.post("/api/upload/avatar", response_model=UploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    session_id: int = Form(...),
):
    try:
        # 检查文件类型
        if file.content_type is None or not file.content_type.startswith(
            ("image/jpeg", "image/png")
        ):
            raise HTTPException(status_code=400, detail="仅支持JPG/PNG格式的图片")

        # 检查文件大小
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        # 生成唯一文件名
        Utils.createDirIfnotExists(Utils.Avatar.get_ai_avatar_dir(session_id))
        file_path = Utils.Avatar.get_ai_avatar_path(session_id, file.filename)
        file_url = Utils.Avatar.get_ai_avatar_url(session_id, file.filename)

        # 删除旧文件
        old_avatar_url = Utils.api.get_session_ai_avatar_url(session_id)
        Utils.Avatar.delete_session_ai_avatar(old_avatar_url)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(contents)

        # 返回成功响应
        await SessionManager.update_session_ai_avatar(session_id, file_url)
        return {"success": True, "file_url": file_url}

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code, content={"success": False, "detail": e.detail}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "detail": f"上传失败: {str(e)}"}
        )


@app.post("/api/upload/user_avatar", response_model=UploadResponse)
async def upload_user_avatar(file: UploadFile = File(...)):
    try:
        # 检查文件类型
        if file.content_type is None or not file.content_type.startswith(
            ("image/jpeg", "image/png")
        ):
            raise HTTPException(status_code=400, detail="仅支持JPG/PNG格式的图片")

        # 检查文件大小
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        # 生成唯一文件名
        Utils.createDirIfnotExists(Utils.Avatar.get_user_avatar_dir())
        file_path = Utils.Avatar.get_user_avatar_path(file.filename)
        file_url = Utils.Avatar.get_user_avatar_url(file.filename)

        # 删除旧文件
        Utils.Avatar.delete_user_avatar()

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(contents)

        # 更新配置
        Utils.Avatar.update_user_avatar_url(file_url)

        # 返回成功响应
        await SessionManager.send_system_config()
        return {"success": True, "file_url": file_url}

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code, content={"success": False, "detail": e.detail}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "detail": f"上传失败: {str(e)}"}
        )


class CommandRequest(BaseModel):
    type: str
    data: dict


@app.post("/api/command")
async def command_command(request: CommandRequest):
    logger.info(f"command command: {request.type}")
    logger.info(f"command data: {request.data}")
    res = await MessageHandler.handle_command_message(request.type, request.data)
    return {"success": res}


# WebSocket 端点
@app.websocket("/ws/aichat/windows")
async def windows_websocket_endpoint(websocket: WebSocket):
    """windows WebSocket端点"""
    await websocket.accept()
    connection_id = int(time.time() * 1000)
    Utils.windows_websockets[connection_id] = websocket
    try:
        # await SessionManager.broadcast_windows_theme()
        while True:
            data = await websocket.receive_text()
            await MessageHandler.handle_windows_message(websocket, data)

    except WebSocketDisconnect:
        logger.info(f"windows WebSocket断开连接")
    except Exception as e:
        logger.error(f"windows WebSocket错误: {e}", exc_info=True)
    finally:
        if connection_id in Utils.windows_websockets:
            del Utils.windows_websockets[connection_id]


@app.websocket("/ws/aichat/electron")
async def electron_websocket_endpoint(websocket: WebSocket):
    """electron WebSocket端点"""
    await websocket.accept()
    connection_id = int(time.time() * 1000)
    Utils.electron_websockets[connection_id] = websocket

    try:
        await SessionManager.broadcast_electron_theme()
        while True:
            data = await websocket.receive_text()
            await MessageHandler.handle_electron_message(websocket, data)

    except WebSocketDisconnect:
        logger.info(f"electron WebSocket断开连接")
    except Exception as e:
        logger.error(f"electron WebSocket错误: {e}", exc_info=True)
    finally:
        if connection_id in Utils.electron_websockets:
            del Utils.electron_websockets[connection_id]


@app.websocket("/ws/aichat/spa")
async def spa_websocket_endpoint(websocket: WebSocket):
    """SPA WebSocket端点"""
    await websocket.accept()
    connection_id = int(time.time() * 1000)
    Utils.spa_websockets[connection_id] = websocket

    try:
        await SessionManager.send_all_sessions()
        await SessionManager.send_system_config()

        while True:
            data = await websocket.receive_text()
            await MessageHandler.handle_spa_message(websocket, data)

    except WebSocketDisconnect:
        logger.info(f"SPA WebSocket断开连接")
    except Exception as e:
        logger.error(f"SPA WebSocket错误: {e}", exc_info=True)
    finally:
        if connection_id in Utils.spa_websockets:
            del Utils.spa_websockets[connection_id]


@app.websocket("/ws/aichat/{clientID}")
async def session_websocket_endpoint(websocket: WebSocket, clientID: int):
    """会话WebSocket端点"""
    await websocket.accept()

    session_id = int(clientID)
    if not Utils.api.is_session_exist(session_id):
        msg = {"type": "error_session_not_exist", "data": {"session_id": session_id}}
        await websocket.send_text(json.dumps(msg))
        await websocket.close()
        return

    connection_id = int(time.time() * 1000)

    if session_id not in Utils.session_websockets:
        Utils.session_websockets[session_id] = {}

    Utils.session_websockets[session_id][connection_id] = websocket

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
        logger.error(f"会话WebSocket {clientID} 错误: {e}", exc_info=True)
    finally:
        if (
            session_id in Utils.session_websockets
            and connection_id in Utils.session_websockets[session_id]
        ):
            del Utils.session_websockets[session_id][connection_id]


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
