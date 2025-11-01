import json
import time
import threading
import asyncio

from fastapi import WebSocket
from libs.log_config import logger
from libs.openai_chat_api import OpenAIChatAPI
from libs.common import Utils
from libs.session_manager import SessionManager

thread_api: OpenAIChatAPI


class MessageHandler:
    """消息处理器，处理不同类型的WebSocket消息"""

    @staticmethod
    async def handle_electron_message(websocket: WebSocket, message_text: str):
        """处理electron WebSocket消息"""
        try:
            message = json.loads(message_text)
            message_type = message["type"]

            logger.warning(f"未知的electron消息类型: {message_type}")
        except Exception as e:
            logger.error(f"处理electron消息时出错: {e}", exc_info=True)

    @staticmethod
    async def handle_spa_message(websocket: WebSocket, message_text: str):
        """处理SPA WebSocket消息"""
        try:
            message = json.loads(message_text)
            message_type = message["type"]
            if not message_type.startswith("parsed_"):
                logger.info(f"接收消息: {message}")
            handlers = {
                "update_theme": MessageHandler._handle_update_theme,
                "update_system_config": MessageHandler._handle_update_system_config,
                "get_all_sessions": MessageHandler._handle_get_all_sessions,
                "create_session": MessageHandler._handle_create_session,
                "copy_session": MessageHandler._handle_copy_session,
                "copy_session_and_message": MessageHandler._handle_copy_session_and_message,
                "update_session_title": MessageHandler._handle_update_session_title,
                "delete_session": MessageHandler._handle_delete_session,
                "update_session_top": MessageHandler._handle_update_session_top,
                "parse_create_session": MessageHandler._handle_parsed_create_session,
            }

            if message_type in handlers:
                await handlers[message_type](websocket, message)
            else:
                logger.warning(f"未知的SPA消息类型: {message_type}")

        except Exception as e:
            logger.error(f"处理SPA消息时出错: {e}", exc_info=True)

    @staticmethod
    async def _handle_update_theme(websocket: WebSocket, message: dict):
        """更新主题"""
        theme = message["data"]["theme"]
        await SessionManager.broadcast_electron_theme(theme)

    @staticmethod
    async def _handle_update_system_config(websocket: WebSocket, message: dict):
        """更新配置"""
        config = message["data"]["system_config"]
        Utils.Config.init_config(config)
        Utils.init_services()
        await SessionManager.send_system_config()

    @staticmethod
    async def _handle_get_all_sessions(websocket: WebSocket, message: dict):
        await SessionManager.send_all_sessions()

    @staticmethod
    async def _handle_create_session(websocket: WebSocket, message: dict):
        system_prompt = Utils.AI_CONFIG_DEFAULT["system_prompt"]
        parsed_system_prompt = json.dumps({"sentences": [], "html": ""})
        title = Utils.AI_CONFIG_DEFAULT["chat_title"]

        config = json.loads(json.dumps(Utils.DEFAULT_AI_CONFIG))
        config["top"] = False
        config["last_active_time"] = time.time()
        config["suggestions"] = []

        session_id, message_id = Utils.api.create_new_session(
            title, config, system_prompt, parsed_system_prompt
        )

        response = {
            "type": "parse_create_session",
            "data": {
                "session_id": session_id,
                "message_id": message_id,
                "raw_text": system_prompt,
            },
        }
        await websocket.send_text(json.dumps(response))

    @staticmethod
    async def _handle_copy_session(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        new_session_id = Utils.api.copy_session(session_id)

        if new_session_id is None:
            raise ValueError("会话复制失败")

        title = Utils.api.get_session_title(session_id)
        config = Utils.api.get_session_ai_config(session_id)
        config["ai_avatar_url"] = Utils.Avatar.copy_session_ai_avatar(
            config["ai_avatar_url"], new_session_id
        )
        config["last_active_time"] = time.time()
        config["suggestions"] = []
        config["top"] = False
        Utils.api.update_session_ai_config(new_session_id, config)

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
        new_session_id = Utils.api.copy_session_and_messages(session_id)

        if new_session_id is None:
            raise ValueError("会话复制失败")

        title = Utils.api.get_session_title(session_id)
        config = Utils.api.get_session_ai_config(session_id)
        config["ai_avatar_url"] = Utils.Avatar.copy_session_ai_avatar(
            config["ai_avatar_url"], new_session_id
        )
        config["last_active_time"] = time.time()
        config["top"] = False
        Utils.api.update_session_ai_config(new_session_id, config)

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
        Utils.api.update_session_property(session_id, "auto_gen_title", False)
        await SessionManager.send_session_config(session_id)

    @staticmethod
    async def _handle_delete_session(websocket: WebSocket, message: dict):
        session_id = message["data"]["session_id"]
        Utils.api.delete_session(session_id)
        Utils.Avatar.remove_session_avatar(session_id)

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

        Utils.api.update_session_top(session_id, top)

        msg = {
            "type": "update_session_top",
            "data": {
                "session_id": session_id,
                "top": top,
            },
        }
        await SessionManager.broadcast_spa(json.dumps(msg))

    @staticmethod
    async def _handle_parsed_create_session(websocket: WebSocket, message: dict):
        data = message["data"]
        message_id = data["message_id"]
        session_id = data["session_id"]
        config = Utils.api.get_session_ai_config(session_id)

        title = Utils.AI_CONFIG_DEFAULT["chat_title"]
        system_prompt = Utils.AI_CONFIG_DEFAULT["system_prompt"]
        parsed_text = {
            "sentences": data["sentences"],
            "html": data["html"],
        }

        Utils.api.update_message(message_id, parsed_text=json.dumps(parsed_text))

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

            if not message_type.startswith("parse"):
                logger.info(f"接收消息: {message}")

            handlers = {
                "user_input": MessageHandler._handle_user_input,
                "parsed_user_message": MessageHandler._handle_parsed_user_message,
                "parsed_ai_response": MessageHandler._handle_parsed_ai_response,
                "stop_response": MessageHandler._handle_stop_response,
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
            logger.error(f"处理会话消息时出错: {e}", exc_info=True)

    @staticmethod
    async def _handle_user_input(websocket: WebSocket, session_id: int, message: dict):
        def handle_user_input():
            asyncio.run(
                MessageHandler._handle_user_input_imple(websocket, session_id, message)
            )

        threading.Thread(
            target=handle_user_input,
            daemon=True,
        ).start()

    @staticmethod
    async def _handle_user_input_imple(
        websocket: WebSocket, session_id: int, message: dict
    ):
        global thread_api
        thread_api = Utils.create_api()
        user_message = message["data"]["user_message"]

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

        is_streaming_closed = False

        async def assistant_response_callback(
            message_id: int, response: str, is_streaming: bool, error: bool = False
        ):
            nonlocal is_streaming_closed
            if is_streaming_closed:
                return
            if not is_streaming:
                is_streaming_closed = True
            msg = {
                "type": "stream_response",
                "data": {
                    "message_id": message_id,
                    "is_streaming": is_streaming,
                    "is_chat_error": error,
                    "response": response,
                },
            }
            await websocket.send_text(json.dumps(msg))

        WITH_SYSTEM_PROMPT = True

        response_dict = await thread_api.chat(
            WITH_SYSTEM_PROMPT,
            session_id,
            user_message,
            json.dumps({"sentences": [], "html": ""}),
            user_message_callback,
            assistant_response_callback,
        )
        if not response_dict:
            return

        response = response_dict["response"]
        message_id = response_dict["message_id"]

        # if not is_streaming_closed:
        #     msg = {
        #         "type": "parse_request",
        #         "data": {
        #             "type": "ai_response",
        #             "data": {"message_id": message_id, "response": response},
        #         },
        #     }
        #     await websocket.send_text(json.dumps(msg))

        if response is None:
            return

        async def system_handle():
            system_info = {}
            if WITH_SYSTEM_PROMPT:
                system_info = response_dict
            else:
                system_prompt_content = thread_api.get_session_system_message(
                    session_id
                )
                system_ai_response = thread_api.system_chat(
                    system_prompt_content, user_message, response
                )
                if system_ai_response is None:
                    return
                system_info = json.loads(system_ai_response)

            title = system_info["title"]
            suggestions = system_info["suggestions"]
            logger.info("标题:%s, 建议:%s", title, suggestions)

            config = thread_api.get_session_ai_config(session_id)
            auto_gen_title = config["auto_gen_title"]
            if auto_gen_title:
                await SessionManager.update_title(session_id, title, thread_api)

            if "secondary_response" in system_info:
                secondary_response = system_info["secondary_response"]
                message = {
                    "type": "secondary_response",
                    "data": {
                        "message_id": message_id,
                        "secondary_response": secondary_response,
                    },
                }
                await websocket.send_text(json.dumps(message))
                parsed_text = thread_api.get_parsed_text(message_id)
                if parsed_text:
                    parsed_text["secondary_response"] = secondary_response
                    thread_api.update_message(
                        message_id,
                        parsed_text=json.dumps(parsed_text, ensure_ascii=False),
                    )

            msg = {
                "type": "session_suggestions",
                "data": {
                    "session_id": session_id,
                    "suggestions": suggestions,
                },
            }
            await websocket.send_text(json.dumps(msg))

            config["last_active_time"] = time.time()
            config["suggestions"] = suggestions
            thread_api.update_session_ai_config(session_id, config)
            await SessionManager.send_session_config(session_id, api=thread_api)
            await SessionManager.send_all_sessions(api=thread_api)

        await system_handle()

    @staticmethod
    async def _handle_parsed_user_message(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        sentences = message["data"]["sentences"]
        html = message["data"]["html"]
        Utils.api.update_message(
            message_id,
            json.dumps({"sentences": sentences, "html": html}, ensure_ascii=False),
        )

    @staticmethod
    async def _handle_parsed_ai_response(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        sentences = message["data"]["sentences"]
        html = message["data"]["html"]
        raw_text = message["data"]["raw_text"]
        Utils.api.update_message(
            message_id,
            json.dumps({"sentences": sentences, "html": html}, ensure_ascii=False),
            raw_text=raw_text,
        )

    @staticmethod
    async def _handle_stop_response(
        websocket: WebSocket, session_id: int, message: dict
    ):
        if thread_api is not None:
            thread_api.stop_response()

    @staticmethod
    async def _handle_update_session_config(
        websocket: WebSocket, session_id: int, message: dict
    ):
        ai_config = message["data"]["ai_config"]
        Utils.api.update_session_ai_config(session_id, ai_config)
        await SessionManager.send_session_config(session_id)

    @staticmethod
    async def _handle_update_message(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        raw_text = message["data"]["raw_text"]
        sentences = message["data"]["sentences"]
        html = message["data"]["html"]

        Utils.speaker.remove_audio_directory(session_id, message_id)
        parsed_text = {"sentences": sentences, "html": html}

        Utils.api.update_message(
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
        Utils.speaker.remove_audio_directory(session_id, message_id)

    @staticmethod
    async def _handle_delete_message(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]

        Utils.api.delete_message(message_id)
        Utils.speaker.remove_audio_directory(session_id, message_id)

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

        await Utils.recognizer.start_recognition(
            websocket, language, input_text, cursor_position
        )

    @staticmethod
    async def _handle_update_cursor_position(
        websocket: WebSocket, session_id: int, message: dict
    ):
        original_text = message["data"]["original_text"]
        cursor_position = message["data"]["cursor_position"]
        Utils.recognizer.reset_text_state(original_text, cursor_position)

    @staticmethod
    async def _handle_stop_speech_recognize(
        websocket: WebSocket, session_id: int, message: dict
    ):
        await Utils.recognizer.stop_recognition()

    @staticmethod
    async def _handle_generate_audio_files(
        websocket: WebSocket, session_id: int, message: dict
    ):
        message_id = message["data"]["message_id"]
        sentence_id_start = message["data"]["sentence_id_start"]
        sentence_id_end = message["data"]["sentence_id_end"]

        ai_config = Utils.api.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]

        sentences = Utils.api.get_sentences(message_id)
        if sentences is None:
            logger.warning(f"消息ID:{message_id} 未找到句子")
            return

        generate_id = int(time.time() * 1000)
        threading.Thread(
            target=Utils.speaker.pregenerate_audio_files,
            args=(
                generate_id,
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

        ai_config = Utils.api.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]

        sentences = Utils.api.get_sentences(message_id)
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
                Utils.speaker.stop_playback()
                logger.error(f"播放回调错误: {e}")

        await play_sentence_callback(-2)

        def play_sentence():
            asyncio.run(
                Utils.speaker.play_sentence(
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

        ai_config = Utils.api.get_session_ai_config(session_id)
        voice_name = ai_config["tts_voice"]
        speech_rate = ai_config["speech_rate"]

        sentences = Utils.api.get_sentences(message_id)
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
        Utils.speaker.pause_playback()

    @staticmethod
    async def _handle_unpause(websocket: WebSocket, session_id: int, message: dict):
        Utils.speaker.resume_playback()

    @staticmethod
    async def _handle_play(websocket: WebSocket, session_id: int, message: dict):
        if Utils.speaker.is_playing():
            Utils.speaker.resume_playback()
        else:
            message_id = message["data"]["message_id"]

            ai_config = Utils.api.get_session_ai_config(session_id)
            voice_name = ai_config["tts_voice"]
            speech_rate = ai_config["speech_rate"]
            sentence_id_start = 0

            sentences = Utils.api.get_sentences(message_id)
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
        Utils.speaker.stop_playback()

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
        last_played_sentence_id = -1
        end_sentence_id = sentences[-1]["sentenceId"]

        async def play_sentence_callback(sentence_id: int):
            nonlocal last_played_sentence_id
            is_need_to_continue_playing = False
            if sentence_id == -2:
                # 播放开始
                pass
            elif sentence_id == -1:
                # 播放结束
                if (
                    last_played_sentence_id != end_sentence_id
                    and not Utils.speaker.is_stopping()
                ):
                    is_need_to_continue_playing = True
            else:
                # 正在播放句子
                last_played_sentence_id = sentence_id

            msg = {
                "type": "the_sentence_playing",
                "data": {
                    "message_id": message_id,
                    "sentence_id": sentence_id,
                },
            }
            try:
                await websocket.send_text(json.dumps(msg))

                if is_need_to_continue_playing:
                    Utils.speaker.stop_playback()
                    logger.warning(
                        f"播放未完成，接着播放，sentenceId={last_played_sentence_id + 1}"
                    )
                    Utils.speaker.stop_generating()
                    await MessageHandler._play_sentences_impl(
                        websocket,
                        session_id,
                        message_id,
                        last_played_sentence_id + 1,
                        sentences,
                        voice_name,
                        speech_rate,
                    )
            except Exception as e:
                Utils.speaker.stop_playback()
                logger.error(f"播放回调错误: {e}")

        await play_sentence_callback(-2)

        def play_sentences():
            asyncio.run(
                Utils.speaker.play_sentences(
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
