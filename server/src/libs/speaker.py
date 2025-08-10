import os

# 设置环境变量以隐藏Pygame支持提示
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import asyncio
import threading
import shutil
import time
from collections import deque
from typing import Dict, Callable, Awaitable, Optional, List
from libs.log_config import logger
import azure.cognitiveservices.speech as speechsdk
import pygame
from pygame import mixer


class SingletonMeta(type):
    """单例模式的元类"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Speaker(metaclass=SingletonMeta):
    """语音合成和播放服务"""

    def __init__(self, config: Dict, voichai_storage_path: str):
        """初始化语音合成器，支持延迟初始化"""
        if not hasattr(self, "_initialized"):
            if config is None:
                raise ValueError("首次初始化需要提供配置")
            self.config = config
            self.voichai_storage_path = voichai_storage_path
            self._initialize()
            self._initialized = True

    def _initialize(self) -> None:
        """初始化语音合成器的内部状态"""
        self.azure_config = self.config["azure"]
        self.speaker_config = self.config["speaker"]
        self._init_audio_system()
        self._audio_generation_lock = threading.Lock()
        self._generate_id = 0
        self._is_stop_generating = False

    def _init_audio_system(self) -> None:
        """初始化Pygame音频系统"""
        pygame.mixer.init(frequency=16000, size=-16, channels=1, buffer=4096)
        self.clock = pygame.time.Clock()
        self.assistant_channel = pygame.mixer.Channel(0)
        self.system_prompt_channel = pygame.mixer.Channel(1)
        self.audio_queue = deque()

    def close(self) -> None:
        """关闭音频系统"""
        pygame.mixer.quit()

    def _get_audio_path(
        self, session_id: int, message_id: int, sentence_id: int
    ) -> str:
        """获取音频文件的完整路径"""
        dir_path = os.path.join(
            self.voichai_storage_path,
            self.speaker_config["audio_dir"],
            str(session_id),
            str(message_id),
        )
        return os.path.join(dir_path, f"{sentence_id}.wav")

    def _create_audio_directory(self, session_id: int, message_id: int) -> None:
        """创建存储音频文件的目录"""
        dir_path = os.path.join(
            self.voichai_storage_path,
            self.speaker_config["audio_dir"],
            str(session_id),
            str(message_id),
        )
        os.makedirs(dir_path, exist_ok=True)

    def remove_audio_directory(self, session_id: int, message_id: int) -> None:
        """删除存储音频文件的目录"""
        dir_path = os.path.join(
            self.voichai_storage_path,
            self.speaker_config["audio_dir"],
            str(session_id),
            str(message_id),
        )
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    def _create_speech_synthesizer(
        self, voice_name: str, output_file: str
    ) -> speechsdk.SpeechSynthesizer:
        """创建Azure语音合成器实例"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.azure_config["key"], region=self.azure_config["region"]
        )
        speech_config.speech_synthesis_voice_name = voice_name
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        return speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

    def _synthesize_speech(
        self,
        synthesizer: speechsdk.SpeechSynthesizer,
        text: str,
        voice_name: str,
        speech_rate: float = 1.0,
    ) -> None:
        """执行语音合成，支持语速调整"""
        if speech_rate == 1.0:
            synthesizer.speak_text(text)
        else:
            ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                    <voice name="{voice_name}">
                        <prosody rate="{int((speech_rate-1)*100)}%">
                            {text}
                        </prosody>
                    </voice>
                </speak>"""
            logger.info(f"SSML: {ssml}")
            synthesizer.speak_ssml(ssml)

    def _generate_audio_file(
        self,
        session_id: int,
        message_id: int,
        sentence_id: int,
        text: str,
        voice_name: str,
        speech_rate: float,
    ) -> mixer.Sound:
        """生成音频文件并返回Pygame Sound对象"""
        audio_path = self._get_audio_path(session_id, message_id, sentence_id)

        if not os.path.isfile(audio_path):
            self._create_audio_directory(session_id, message_id)
            synthesizer = self._create_speech_synthesizer(voice_name, audio_path)
            self._synthesize_speech(synthesizer, text, voice_name, speech_rate)

        return mixer.Sound(audio_path)

    def pregenerate_audio_files(
        self,
        generate_id: int,
        session_id: int,
        message_id: int,
        sentences: List[Dict],
        voice_name: str,
        speech_rate: float,
    ) -> None:
        """预生成一系列音频文件"""
        with self._audio_generation_lock:
            self._generate_id = generate_id
            self.audio_queue.clear()
            for sentence in sentences:
                sentence_id = sentence.get("sentenceId", -1)
                text = sentence.get("text", "")
                if sentence_id != -1 and text:
                    try:
                        sound = self._generate_audio_file(
                            session_id,
                            message_id,
                            sentence_id,
                            text,
                            voice_name,
                            speech_rate,
                        )
                        self.audio_queue.append((sentence_id, sound))
                    except Exception as e:
                        logger.error(f"生成音频文件失败: {e}")
                    if self._is_stop_generating:
                        self._is_stop_generating = False
                        break

    def pause_playback(self) -> None:
        """暂停语音播放"""
        self.assistant_channel.pause()

    def resume_playback(self) -> None:
        """恢复语音播放"""
        self.assistant_channel.unpause()

    def is_playing(self) -> bool:
        """检查是否正在播放语音"""
        return self.assistant_channel.get_busy()

    def stop_playback(self) -> None:
        """停止语音播放"""
        self.audio_queue.clear()
        self.assistant_channel.stop()

    def stop_generating(self) -> None:
        """停止生成音频"""
        self._is_stop_generating = True

    async def play_sentence(
        self,
        session_id: int,
        message_id: int,
        sentence_id: int,
        sentences: List[Dict],
        callback: Callable[[int], Awaitable[None]],
        voice_name: str,
        speech_rate: float,
    ) -> None:
        """播放单个句子"""
        sentence_text = next(
            (s["text"] for s in sentences if s.get("sentenceId") == sentence_id),
            "",
        )
        if not sentence_text:
            logger.warning(f"未找到句子ID {sentence_id} 的文本")
            return

        await self._play_audio(
            session_id,
            message_id,
            sentence_id,
            sentence_text,
            callback,
            voice_name,
            speech_rate,
        )

    async def play_sentences(
        self,
        session_id: int,
        message_id: int,
        start_id: int,
        sentences: List[Dict],
        callback: Callable[[int], Awaitable[None]],
        voice_name: str,
        speech_rate: float,
    ) -> None:
        """连续播放多个句子"""
        self.stop_playback()
        generate_id = int(time.time() * 1000)
        # 生成并排队所有音频
        threading.Thread(
            target=self.pregenerate_audio_files,
            args=(
                generate_id,
                session_id,
                message_id,
                sentences[start_id:],
                voice_name,
                speech_rate,
            ),
            daemon=True,
        ).start()

        while self._generate_id != generate_id or len(self.audio_queue) == 0:
            await asyncio.sleep(0.1)
        current_id, current_sound = self.audio_queue.popleft()
        sentence_id_playing = current_id
        self.assistant_channel.play(current_sound)
        await callback(current_id)
        had_queue = False
        while self.assistant_channel.get_busy():
            if self.assistant_channel.get_queue():
                had_queue = True
            else:
                if len(self.audio_queue) == 0:
                    if had_queue:
                        had_queue = False
                        sentence_id_playing += 1
                        await callback(sentence_id_playing)
                else:
                    current_id, current_sound = self.audio_queue.popleft()
                    self.assistant_channel.queue(current_sound)
                    if had_queue:
                        sentence_id_playing += 1
                        await callback(sentence_id_playing)
            await asyncio.sleep(0.1)
        await callback(-1)  # 播放结束

    async def _play_audio(
        self,
        session_id: int,
        message_id: int,
        sentence_id: int,
        text: str,
        callback: Callable[[int], Awaitable[None]],
        voice_name: str,
        speech_rate: float,
    ) -> None:
        """内部方法：播放单个音频文件"""
        self.stop_playback()

        # 生成音频文件
        generate_id = int(time.time() * 1000)
        self.pregenerate_audio_files(
            generate_id,
            session_id,
            message_id,
            [{"sentenceId": sentence_id, "text": text}],
            voice_name,
            speech_rate,
        )

        _, sound = self.audio_queue.popleft()
        # 播放音频
        self.assistant_channel.play(sound)
        await callback(int(sentence_id))

        # 等待播放完成
        while self.is_playing():
            await asyncio.sleep(0.1)

        await callback(-1)
