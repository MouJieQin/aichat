import json
import os
import appdirs
import shutil
from fastapi import WebSocket
from typing import Dict
from libs.log_config import logger


class UtilsBase:
    # 路径配置
    SERVER_SRC_ABS_PATH = os.path.abspath(os.getcwd())
    APP_SUPPORT_PATH = appdirs.user_data_dir()[0:-1]
    VOICHAI_SUPPORT_PATH = f"{APP_SUPPORT_PATH}/voichai"
    VOICHAI_STORAGE_PATH = f"{VOICHAI_SUPPORT_PATH}/Voichai-Storage"
    USER_CONFIG_DIR = VOICHAI_STORAGE_PATH + "/config"
    CONFIG_FILE = USER_CONFIG_DIR + "/config.json"
    DEFAULT_CONFIG_FILE = SERVER_SRC_ABS_PATH + "/config.json"
    DATA_PATH = VOICHAI_STORAGE_PATH + "/data"
    AVATARS_PATH = DATA_PATH + "/avatars"
    DATABASE_PATH = DATA_PATH + "/chat-history.db"
    AVATAR_BASE_URL = "/api/download?path=/avatars"

    DEFAULT_CONFIG = {}
    CONFIG = {}
    AI_CONFIG = {}
    AI_CONFIG_DEFAULT = {}
    APIS = []
    DEFAULT_AI_CONFIG = {}
    SYSTEM_AI_CONFIG = {}

    # WebSocket 连接管理
    electron_websockets: Dict[int, WebSocket] = {}
    spa_websockets: Dict[int, WebSocket] = {}
    session_websockets: Dict[int, Dict[int, WebSocket]] = {}

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

    class Config:
        @staticmethod
        def syncConfig():
            """同步配置文件"""
            with open(UtilsBase.CONFIG_FILE, mode="w", encoding="utf-8") as f:
                f.write(json.dumps(UtilsBase.CONFIG, ensure_ascii=False, indent=4))

        @staticmethod
        def init_config(config: dict):
            """初始化配置目录和文件"""
            UtilsBase.CONFIG = config
            UtilsBase.Config.syncConfig()

            UtilsBase.AI_CONFIG = UtilsBase.CONFIG["ai_assistant"]
            UtilsBase.AI_CONFIG_DEFAULT = UtilsBase.AI_CONFIG["default"]
            UtilsBase.APIS = UtilsBase.AI_CONFIG["apis"]

            def find_index_by_name(name: str):
                for i in range(len(UtilsBase.APIS)):
                    if UtilsBase.APIS[i].get("name") == name:
                        return i
                return -1  # 若未找到则返回 -1

            DEFAULT_AI_CONFIG_index = find_index_by_name(
                UtilsBase.AI_CONFIG_DEFAULT["ai_config_name"]
            )
            UtilsBase.DEFAULT_AI_CONFIG = UtilsBase.APIS[DEFAULT_AI_CONFIG_index]

            SYSTEM_AI_CONFIG_index = find_index_by_name(
                UtilsBase.AI_CONFIG["system_ai_config"]["ai_config_name"]
            )
            UtilsBase.SYSTEM_AI_CONFIG = UtilsBase.APIS[SYSTEM_AI_CONFIG_index]


def init_config():
    """初始化配置目录和文件"""
    UtilsBase.createDirIfnotExists(UtilsBase.USER_CONFIG_DIR)
    UtilsBase.createDirIfnotExists(UtilsBase.DATA_PATH)
    UtilsBase.createDirIfnotExists(UtilsBase.AVATARS_PATH)

    with open(UtilsBase.DEFAULT_CONFIG_FILE, mode="r", encoding="utf-8") as f:
        UtilsBase.DEFAULT_CONFIG = json.load(f)

    if os.path.isfile(UtilsBase.CONFIG_FILE):
        with open(UtilsBase.CONFIG_FILE, mode="r", encoding="utf-8") as f:
            UtilsBase.CONFIG = json.load(f)
    else:
        UtilsBase.CONFIG = {}

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

    setDefaultValIfNone(UtilsBase.CONFIG, UtilsBase.DEFAULT_CONFIG)

    if diff_flag:
        logger.info("配置文件缺失部分项，已使用默认值填充")
        logger.info(f"配置文件: {UtilsBase.CONFIG_FILE}")
        logger.info(f"默认配置: {UtilsBase.DEFAULT_CONFIG_FILE}")

        UtilsBase.Config.syncConfig()

    UtilsBase.Config.init_config(UtilsBase.CONFIG)


init_config()
