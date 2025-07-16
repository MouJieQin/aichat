import json
import os
import appdirs
from fastapi import WebSocket
from typing import Dict
from libs.log_config import logger
from libs.chat_database import ChatDatabase
from libs.openai_chat_api import OpenAIChatAPI
from libs.speaker import Speaker
from libs.recognizer import Recognizer

# 路径配置
SERVER_SRC_ABS_PATH = os.path.abspath(os.getcwd())
APP_SUPPORT_PATH = app_support_path = appdirs.user_data_dir()[0:-1]
VOICHAI_SUPPORT_PATH = f"{APP_SUPPORT_PATH}/voichai"
VOICHAI_STORAGE_PATH = f"{VOICHAI_SUPPORT_PATH}/Voichai-Storage"
USER_CONFIG_DIR = VOICHAI_STORAGE_PATH + "/config"
CONFIG_FILE = USER_CONFIG_DIR + "/config.json"
DEFAULT_CONFIG_FILE = SERVER_SRC_ABS_PATH + "/config.json"
DATA_PATH = VOICHAI_STORAGE_PATH + "/data"
DATABASE_PATH = DATA_PATH + "/chat-history.db"

CONFIG = {}
DEFAULT_CONFIG = {}

# WebSocket 连接管理
spa_websockets: Dict[int, WebSocket] = {}
session_websockets: Dict[int, Dict[int, WebSocket]] = {}


def create_api() -> OpenAIChatAPI:
    db = ChatDatabase(DATABASE_PATH)
    api = OpenAIChatAPI(AI_CONFIG, db)
    return api


def init_config():
    """初始化配置目录和文件"""
    global CONFIG, DEFAULT_CONFIG

    def createDirIfnotExists(path: str):
        if not os.path.exists(path):
            os.makedirs(path)

    createDirIfnotExists(USER_CONFIG_DIR)
    createDirIfnotExists(DATA_PATH)

    with open(DEFAULT_CONFIG_FILE, mode="r", encoding="utf-8") as f:
        DEFAULT_CONFIG = json.load(f)

    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, mode="r", encoding="utf-8") as f:
            CONFIG = json.load(f)
    else:
        CONFIG = {}

    diff_flag = False

    # 检查配置项是否缺失，并使用默认值填充
    def setDefaultValIfNone(config: dict, defaultConfig: dict):
        nonlocal diff_flag
        for key, default_val in defaultConfig.items():
            if key not in config:
                diff_flag = True
                config[key] = default_val
            else:
                if isinstance(default_val, dict):
                    setDefaultValIfNone(config[key], default_val)

    setDefaultValIfNone(CONFIG, DEFAULT_CONFIG)

    if diff_flag:
        logger.info("配置文件缺失部分项，已使用默认值填充")
        logger.info(f"配置文件: {CONFIG_FILE}")
        logger.info(f"默认配置: {DEFAULT_CONFIG_FILE}")

        def syncConfig():
            with open(CONFIG_FILE, mode="w", encoding="utf-8") as f:
                f.write(json.dumps(CONFIG, ensure_ascii=False, indent=4))

        syncConfig()


init_config()
AI_CONFIG = CONFIG["ai_assistant"]
AI_CONFIG_DEFAULT = AI_CONFIG["default"]
DEFAULT_AI_CONFIG = AI_CONFIG[AI_CONFIG_DEFAULT["ai_config_name"]]

# 初始化服务
db = ChatDatabase(DATABASE_PATH)
api = OpenAIChatAPI(AI_CONFIG, db)
speaker = Speaker(CONFIG, VOICHAI_STORAGE_PATH)
recognizer = Recognizer(CONFIG)
