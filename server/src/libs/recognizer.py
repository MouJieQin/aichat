import azure.cognitiveservices.speech as speechsdk
from typing import Dict, Callable, Optional
from libs.log_config import logger
from fastapi import WebSocket
import json
import asyncio


class Recognizer:
    """Azure 语音识别服务封装类"""

    def __init__(self, config: Dict):
        """初始化语音识别器"""
        self.azure_config = config["azure"]
        self.speech_config = self._create_speech_config()
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer: Optional[speechsdk.SpeechRecognizer] = None
        self.websocket: Optional[WebSocket] = None
        self.text_state = TextState()

    def _create_speech_config(self) -> speechsdk.SpeechConfig:
        """创建语音配置"""
        config = speechsdk.SpeechConfig(
            subscription=self.azure_config["key"],
            region=self.azure_config["region"],
            speech_recognition_language="zh-CN",
        )
        # 可以在这里添加其他配置选项
        return config

    async def _send_message(self, message: Dict) -> None:
        """异步发送消息到WebSocket客户端"""
        if self.websocket:
            try:
                await self.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                self.websocket = None
                await self.stop_recognition()

    async def _send_recognition_update(self, recognized_text: str) -> None:
        """发送识别文本更新到客户端"""
        message = {
            "type": "speech_recognizing",
            "data": {
                "stt_text": self.text_state.get_combined_text(recognized_text),
                "cursor_position": self.text_state.get_cursor_position(recognized_text),
            },
        }
        await self._send_message(message)

    def _handle_recognizing(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        """处理正在识别事件"""
        text = evt.result.text
        asyncio.run(self._send_recognition_update(text))
        logger.info(f"识别中: {text}")

    def _handle_recognized(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        """处理识别完成事件"""
        text = evt.result.text
        asyncio.run(self._send_recognition_update(text))
        self.text_state.update(text)
        logger.info(f"识别完成: {text}")

    def _handle_session_started(self, evt: speechsdk.SessionEventArgs) -> None:
        """处理会话开始事件"""
        message = {
            "type": "speech_recognizing",
            "data": {
                "stt_text": self.text_state.get_full_text(),
                "cursor_position": self.text_state.cursor_position,
            },
        }
        asyncio.run(self._send_message(message))
        logger.info(f"会话开始: {evt}")

    def _handle_session_stopped(self, evt: speechsdk.SessionEventArgs) -> None:
        """处理会话停止事件"""
        asyncio.run(self._send_message({"type": "stop_speech_recognize", "data": {}}))
        logger.info(f"会话停止: {evt}")
        self.speech_recognizer = None

    def _handle_canceled(
        self, evt: speechsdk.SpeechRecognitionCanceledEventArgs
    ) -> None:
        """处理识别取消事件"""
        reason = evt.result.cancellation_details.reason
        if reason == speechsdk.CancellationReason.EndOfStream:
            logger.warning(f"会话因流结束被取消: {reason}")
        elif reason == speechsdk.CancellationReason.Error:
            logger.error(f"会话因错误被取消: {reason}")
        else:
            logger.warning(f"会话被取消: {reason}")
        asyncio.run(self._send_message({"type": "stop_speech_recognize", "data": {}}))
        self.speech_recognizer = None

    async def stop_recognition(self) -> None:
        """异步停止语音识别"""
        if self.speech_recognizer:
            try:
                self.speech_recognizer.stop_continuous_recognition()
            except Exception as e:
                logger.error(f"停止识别失败: {e}")
            finally:
                self.speech_recognizer = None

    def reset_text_state(self, original_text: str, cursor_position: int) -> None:
        """重置文本状态"""
        self.text_state.reset(original_text, cursor_position)

    async def start_recognition(
        self,
        websocket: WebSocket,
        language: str,
        original_text: str,
        cursor_position: int,
    ) -> None:
        """异步启动语音识别"""
        await self.stop_recognition()

        # 更新配置和状态
        self.speech_config.speech_recognition_language = language
        self.text_state.reset(original_text, cursor_position)
        self.websocket = websocket

        # 创建并配置识别器
        self.speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )

        # 注册事件处理程序
        self.speech_recognizer.recognizing.connect(self._handle_recognizing)
        self.speech_recognizer.recognized.connect(self._handle_recognized)
        self.speech_recognizer.session_started.connect(self._handle_session_started)
        self.speech_recognizer.session_stopped.connect(self._handle_session_stopped)
        self.speech_recognizer.canceled.connect(self._handle_canceled)

        # 启动连续识别
        try:
            self.speech_recognizer.start_continuous_recognition()
        except Exception as e:
            logger.error(f"启动识别失败: {e}")
            self.speech_recognizer = None
            raise


class TextState:
    """管理识别文本的状态"""

    def __init__(self):
        self.prefix_text = ""
        self.suffix_text = ""
        self.cursor_position = 0

    def reset(self, original_text: str, cursor_position: int) -> None:
        """重置文本状态"""
        self.prefix_text = original_text[:cursor_position]
        self.suffix_text = original_text[cursor_position:]
        self.cursor_position = cursor_position

    def update(self, recognized_text: str) -> None:
        """更新文本状态"""
        self.prefix_text += recognized_text
        self.cursor_position += len(recognized_text)

    def get_combined_text(self, recognized_text: str) -> str:
        """获取组合后的完整文本"""
        return self.prefix_text + recognized_text + self.suffix_text

    def get_cursor_position(self, recognized_text: str) -> int:
        """获取光标位置"""
        return self.cursor_position + len(recognized_text)

    def get_full_text(self) -> str:
        """获取完整文本"""
        return self.prefix_text + self.suffix_text
