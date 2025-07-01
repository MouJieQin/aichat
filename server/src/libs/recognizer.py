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

        self.websocket: Optional[WebSocket] = None

    def _azure_stt_input_auto_recognizing(self, evt):
        cur_recognized_text = evt.result.text
        size = len(cur_recognized_text)
        msg = {
            "type": "start_speech_recognize",
            "data": {
                "stt_text": self.prefix_text + cur_recognized_text + self.suffix_text,
                "cursor_position": self.prefix_cursor_position + size,
            },
        }

        if self.websocket:
            asyncio.run(self.websocket.send_text(json.dumps(msg)))
        logger.info("RECOGNIZING: {}".format(cur_recognized_text))

    def _azure_stt_input_auto_recognized(self, evt):
        cur_recognized_text = evt.result.text
        size = len(cur_recognized_text)
        logger.info("RECOGNIZED: {}".format(cur_recognized_text))

    def _azure_auto_stt_recognizer_session_started(self, evt):
        logger.info(f"SESSION STARTED : {evt}")

    def _azure_auto_stt_recognizer_session_stopped(self, evt):
        logger.info(f"SESSION STOPPED : {evt}")

    def _azure_auto_stt_recognizer_canceled(self, evt):
        logger.info(f"SESSION CANCELED : {evt}")
        detailed_reason = evt.result.cancellation_details.reason
        if detailed_reason == speechsdk.CancellationReason.EndOfStream:
            logger.warning(f"SESSION CANCELED : {detailed_reason}")
        elif detailed_reason == speechsdk.CancellationReason.Error:
            logger.error(f"SESSION CANCELED : {detailed_reason}")
        else:
            logger.warning(f"SESSION CANCELED : {detailed_reason}")

    def stop_recognizer(self):
        self.speech_recognizer.stop_continuous_recognition()

    def stop_recognizer_sync(self):
        self.speech_recognizer.stop_continuous_recognition()

    def start_recognizer(
        self,
        websocket: WebSocket,
        speech_recognition_language: str,
        original_text: str,
        original_cursor_position: int,
    ):
        self.speech_config.speech_recognition_language = speech_recognition_language
        self.prefix_text = original_text[0:original_cursor_position]
        self.suffix_text = original_text[original_cursor_position:]
        self.prefix_cursor_position = original_cursor_position
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
