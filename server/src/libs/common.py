import os
import shutil
from typing import Dict, Optional
from libs.chat_database import ChatDatabase
from libs.openai_chat_api import OpenAIChatAPI
from libs.speaker import Speaker
from libs.recognizer import Recognizer
from libs.config import UtilsBase
from libs.config import (
    AVATARS_PATH,
    AVATAR_BASE_URL,
    CONFIG,
    DATABASE_PATH,
    AI_CONFIG,
    VOICHAI_STORAGE_PATH,
)


class Utils(UtilsBase):
    class Avatar:
        @staticmethod
        def get_ai_avatar_dir(session_id: int):
            return AVATARS_PATH + f"/{session_id}"

        @staticmethod
        def get_ai_avatar_filename(orginal_filename: Optional[str]):
            return f"ai-{orginal_filename}"

        @staticmethod
        def get_ai_avatar_path(session_id: int, filename: Optional[str]):
            filename = Utils.Avatar.get_ai_avatar_filename(filename)
            return Utils.Avatar.get_ai_avatar_dir(session_id) + f"/{filename}"

        @staticmethod
        def get_ai_avatar_url(session_id: int, filename: Optional[str]):
            filename = Utils.Avatar.get_ai_avatar_filename(filename)
            return f"{AVATAR_BASE_URL}/{session_id}/{filename}"

        @staticmethod
        def get_filename_from_ai_avatar_url(ai_avatar_url: str) -> tuple[int, str]:
            session_id, filename = ai_avatar_url.split("/")[-2:]
            return int(session_id), filename

        @staticmethod
        def get_path_from_ai_avatar_url(ai_avatar_url: str) -> str:
            session_id, filename = Utils.Avatar.get_filename_from_ai_avatar_url(
                ai_avatar_url
            )
            return Utils.Avatar.get_ai_avatar_dir(session_id) + f"/{filename}"

        @staticmethod
        def delete_session_ai_avatar(ai_avatar_url: Optional[str]):
            if ai_avatar_url:
                Utils.removeFileIfExists(
                    Utils.Avatar.get_path_from_ai_avatar_url(ai_avatar_url)
                )

        @staticmethod
        def copy_session_ai_avatar(ai_avatar_url: str, session_id: int) -> str:
            if not ai_avatar_url:
                return ""
            avatar_dir = Utils.Avatar.get_ai_avatar_dir(session_id)
            Utils.createDirIfnotExists(avatar_dir)
            src_avatar_path = Utils.Avatar.get_path_from_ai_avatar_url(ai_avatar_url)
            _, filename = Utils.Avatar.get_filename_from_ai_avatar_url(ai_avatar_url)
            shutil.copyfile(src_avatar_path, avatar_dir + f"/{filename}")
            return f"{AVATAR_BASE_URL}/{session_id}/{filename}"

        @staticmethod
        def remove_session_avatar(session_id: int):
            dir = Utils.Avatar.get_ai_avatar_dir(session_id)
            Utils.removeDirIfExists(dir)

    @staticmethod
    def create_api() -> OpenAIChatAPI:
        db = ChatDatabase(DATABASE_PATH)
        api = OpenAIChatAPI(db)
        return api


# 初始化服务
db = ChatDatabase(DATABASE_PATH)
api = OpenAIChatAPI(db)
speaker = Speaker(CONFIG, VOICHAI_STORAGE_PATH)
recognizer = Recognizer(CONFIG)
