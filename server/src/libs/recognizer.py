import azure.cognitiveservices.speech as speechsdk
from typing import Dict, Callable, Optional
from libs.log_config import logger
from fastapi import WebSocket
import json
import asyncio


class Recognizer:
    def __init__(self, configure: Dict):
        self.azure_config = configure["azure"]
        self.azure_key = self.azure_config["key"]
        self.azure_region = self.azure_config["region"]
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.azure_key,
            region=self.azure_region,
            speech_recognition_language="zh-CN",
        )
        self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer: Optional[speechsdk.SpeechRecognizer] = None
        self.websocket: Optional[WebSocket] = None
        self.prefix_text = ""
        self.suffix_text = ""
        self.cursor_position = 0

    def _send_text(self, msg: Dict):
        if self.websocket:
            asyncio.run(self.websocket.send_text(json.dumps(msg)))

    def _send_recognized_text(self, recognized_text: str):
        size = len(recognized_text)
        msg = {
            "type": "speech_recognizing",
            "data": {
                "stt_text": self.prefix_text + recognized_text + self.suffix_text,
                "cursor_position": self.cursor_position + size,
            },
        }
        self._send_text(msg)

    def _azure_stt_input_auto_recognizing(self, evt):
        cur_recognized_text = evt.result.text
        self._send_recognized_text(cur_recognized_text)
        logger.info("RECOGNIZING: {}".format(cur_recognized_text))

    def _azure_stt_input_auto_recognized(self, evt):
        cur_recognized_text = evt.result.text
        self._send_recognized_text(cur_recognized_text)
        self.prefix_text += cur_recognized_text
        self.cursor_position += len(cur_recognized_text)
        logger.info("RECOGNIZED: {}".format(cur_recognized_text))

    def _azure_auto_stt_recognizer_session_started(self, evt):
        msg = {
            "type": "speech_recognizing",
            "data": {
                "stt_text": self.prefix_text + self.suffix_text,
                "cursor_position": self.cursor_position,
            },
        }
        self._send_text(msg)
        logger.info(f"SESSION STARTED : {evt}")

    def _send_stopped_msg(self):
        msg = {
            "type": "stop_speech_recognize",
            "data": {},
        }
        self._send_text(msg)

    def _azure_auto_stt_recognizer_session_stopped(self, evt):
        self._send_stopped_msg()
        logger.info(f"SESSION STOPPED : {evt}")

    def _azure_auto_stt_recognizer_canceled(self, evt):
        self._send_stopped_msg()
        detailed_reason = evt.result.cancellation_details.reason
        if detailed_reason == speechsdk.CancellationReason.EndOfStream:
            logger.warning(f"SESSION CANCELED with EndOfStream: {detailed_reason}")
        elif detailed_reason == speechsdk.CancellationReason.Error:
            logger.error(f"SESSION CANCELED With Error : {detailed_reason}")
        else:
            logger.warning(f"SESSION CANCELED : {detailed_reason}")

    def stop_recognizer_asyn(self):
        if self.speech_recognizer:
            self.speech_recognizer.stop_continuous_recognition_async()
            self.speech_recognizer = None

    def stop_recognizer_sync(self):
        if self.speech_recognizer:
            self.speech_recognizer.stop_continuous_recognition()
            self.speech_recognizer = None

    def start_recognizer(
        self,
        websocket: WebSocket,
        speech_recognition_language: str,
        original_text: str,
        original_cursor_position: int,
    ):
        self.stop_recognizer_sync()

        self.speech_config.speech_recognition_language = speech_recognition_language
        self.prefix_text = original_text[0:original_cursor_position]
        self.suffix_text = original_text[original_cursor_position:]
        self.cursor_position = original_cursor_position
        self.websocket = websocket

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, audio_config=self.audio_config
        )
        speech_recognizer.recognizing.connect(self._azure_stt_input_auto_recognizing)
        speech_recognizer.recognized.connect(self._azure_stt_input_auto_recognized)
        speech_recognizer.session_started.connect(
            self._azure_auto_stt_recognizer_session_started
        )
        speech_recognizer.session_stopped.connect(
            self._azure_auto_stt_recognizer_session_stopped
        )
        speech_recognizer.canceled.connect(self._azure_auto_stt_recognizer_canceled)
        self.speech_recognizer = speech_recognizer
        self.speech_recognizer.start_continuous_recognition()
