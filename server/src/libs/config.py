import json
import os
import appdirs
import shutil
from fastapi import WebSocket
from typing import Dict
from libs.log_config import logger

# 路径配置
SERVER_SRC_ABS_PATH = os.path.abspath(os.getcwd())
APP_SUPPORT_PATH = app_support_path = appdirs.user_data_dir()[0:-1]
VOICHAI_SUPPORT_PATH = f"{APP_SUPPORT_PATH}/voichai"
VOICHAI_STORAGE_PATH = f"{VOICHAI_SUPPORT_PATH}/Voichai-Storage"
USER_CONFIG_DIR = VOICHAI_STORAGE_PATH + "/config"
CONFIG_FILE = USER_CONFIG_DIR + "/config.json"
DEFAULT_CONFIG_FILE = SERVER_SRC_ABS_PATH + "/config.json"
DATA_PATH = VOICHAI_STORAGE_PATH + "/data"
AVATARS_PATH = DATA_PATH + "/avatars"
DATABASE_PATH = DATA_PATH + "/chat-history.db"
AVATAR_BASE_URL = "/api/download?path=/avatars"

CONFIG = {}
DEFAULT_CONFIG = {}

# WebSocket 连接管理
spa_websockets: Dict[int, WebSocket] = {}
session_websockets: Dict[int, Dict[int, WebSocket]] = {}


class UtilsBase:
    @staticmethod
    def createDirIfnotExists(path: str):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def removeDirIfExists(path: str):
        if os.path.exists(path):
            shutil.rmtree(path)

    @staticmethod
    def removeFileIfExists(path: str):
        if os.path.exists(path):
            os.remove(path)


def init_config():
    """初始化配置目录和文件"""
    global CONFIG, DEFAULT_CONFIG

    UtilsBase.createDirIfnotExists(USER_CONFIG_DIR)
    UtilsBase.createDirIfnotExists(DATA_PATH)
    UtilsBase.createDirIfnotExists(AVATARS_PATH)

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
APIS = AI_CONFIG["apis"]


def find_index_by_name(name: str):
    for i in range(len(APIS)):
        if APIS[i].get("name") == name:
            return i
    return -1  # 若未找到则返回 -1


DEFAULT_AI_CONFIG_index = find_index_by_name(AI_CONFIG_DEFAULT["ai_config_name"])
DEFAULT_AI_CONFIG = APIS[DEFAULT_AI_CONFIG_index]

SYSTEM_AI_CONFIG_index = find_index_by_name(
    AI_CONFIG["system_ai_config"]["ai_config_name"]
)
SYSTEM_AI_CONFIG = APIS[SYSTEM_AI_CONFIG_index]
