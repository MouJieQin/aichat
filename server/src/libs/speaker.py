import os

# Set the environment variable before importing pygame
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from pygame import mixer
from collections import deque
import threading
import asyncio
from typing import Dict, Callable, Awaitable, Optional
from libs.log_config import logger
import azure.cognitiveservices.speech as speechsdk
import time
import shutil

class PygameAudioOutputStream(speechsdk.audio.PushAudioOutputStreamCallback):
    """
    A custom audio output stream that passes speech data to Pygame.
    """

    def __init__(self, audio_channel: pygame.mixer.Channel):
        super().__init__()
        # Memory stream handle: buffer to accumulate audio data
        self._audio_buffer = bytearray()
        # Queue to store Pygame sound objects
        self.audio_queue = deque()
        # Pygame clock object for timing control
        self.clock = pygame.time.Clock()
        # Pygame audio channel for playback
        self.audio_channel = audio_channel
        # Size of each audio chunk to process
        self.CHUNK_SIZE = 192000

    def write(self, audio_buffer: memoryview) -> int:
        """
        Implement the write method to add audio data to the Pygame audio queue.

        Args:
            audio_buffer (memoryview): A memory view of the audio data to be written.

        Returns:
            int: The length of the audio buffer written.
        """
        audio_data = bytes(audio_buffer)
        self._audio_buffer.extend(audio_data)

        # Process the buffer when it accumulates enough data
        while len(self._audio_buffer) >= self.CHUNK_SIZE:
            self._process_audio_chunk()

        return len(audio_buffer)

    def _process_audio_chunk(self):
        """
        Process an audio chunk from the buffer, create a Pygame sound object,
        and add it to the playback queue or play it immediately.
        """
        try:
            # Extract a chunk from the buffer
            chunk = self._audio_buffer[: self.CHUNK_SIZE]
            self._audio_buffer = self._audio_buffer[self.CHUNK_SIZE :]

            # Create a Pygame sound object
            sound = self._create_sound_from_chunk(chunk)

            if not self.audio_channel.get_busy():
                # Play the sound immediately if the channel is idle
                self.audio_channel.play(sound)
            else:
                # Queue the sound if the channel is busy
                self.audio_queue.append(sound)
        except Exception as e:
            logger.exception(f"Error creating sound chunk: {e}")

    def _create_sound_from_chunk(self, chunk: bytes) -> pygame.mixer.Sound:
        """
        Create a Pygame sound object from an audio chunk.

        Args:
            chunk (bytes): A byte array representing an audio chunk.

        Returns:
            pygame.mixer.Sound: A Pygame sound object created from the chunk.
        """
        return pygame.sndarray.make_sound(
            pygame.sndarray.array(pygame.mixer.Sound(buffer=chunk))
        )

    def close(self) -> None:
        """关闭流时的清理工作"""
        self._audio_data = bytearray()
        logger.info("Audio stream closed")

    def handel_tail(self):
        if self._audio_buffer:
            try:
                sound = pygame.sndarray.make_sound(
                    pygame.sndarray.array(pygame.mixer.Sound(buffer=self._audio_buffer))
                )
                self._audio_buffer = bytearray()  # 清空缓冲区
                if self.audio_channel.get_busy():
                    self.audio_queue.append(sound)
                else:
                    self.audio_channel.play(sound)  # 直接播放
                while self.audio_channel.get_busy():
                    if not self.audio_channel.get_queue() and len(self.audio_queue) > 0:
                        self.audio_channel.queue(self.audio_queue.popleft())
                    time.sleep(0.1)
            except Exception as e:
                logger.exception(f"Error processing remaining audio: {e}")


class SingletonMeta(type):
    """
    Metaclass for implementing the Singleton pattern.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Speaker(metaclass=SingletonMeta):
    def __init__(self, configure: Dict):

        # Ensure initialization only happens once
        if not hasattr(self, "_initialized"):
            if configure is None:
                raise ValueError("config must be provided on first initialization")
            self.configure = configure
            self._init()
            self._initialized = True

    def _init(self):
        self.audio_files = {
            "start_record": "./voices/BubbleAppear.aiff.wav",
            "end_record": "./voices/BubbleDisappear.aiff.wav",
            "send_message": "./voices/SentMessage.aiff.wav",
            "receive_response": "./voices/Blow.aiff.wav",
        }
        self.azure_config = self.configure["azure"]
        self.azure_key = self.azure_config["key"]
        self.azure_region = self.azure_config["region"]
        self.speaker_config = self.configure["speaker"]
        # Cache loaded audio files
        self.audio_cache = {}
        self._init_mixer()
        self._init_speech_synthesizer()
        self.lock = threading.Lock()

    def _init_mixer(self):
        """Initialize the Pygame mixer."""
        device_name = self.speaker_config["ai_assistant"]["device_name"]
        pygame.mixer.init(
            frequency=16000, size=-16, channels=1, buffer=4096, devicename=device_name
        )
        self.clock = pygame.time.Clock()
        self.audio_channel_assistant_synthesizer = pygame.mixer.Channel(0)
        self.audio_channel_system_prompt = pygame.mixer.Channel(1)

        # self.keep_alive_channel = pygame.mixer.Channel(2)
        # self.keep_alive_channel.set_volume(0.05)
        # self.silent_sound = mixer.Sound(self.audio_files["send_message"])
        # self.silent_sound.set_volume(0.05)
        self.audio_queue = deque()

    def close(self):
        """Close the Pygame mixer."""
        pygame.mixer.quit()

    def stop_playback(self):
        """Stop assistant playback channels."""
        self.audio_channel_assistant_synthesizer.stop()

    def _init_speech_synthesizer(self, voice_name: str = "zh-CN-XiaochenNeural"):
        """Initialize the speech synthesizer."""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.azure_key, region=self.azure_region
        )

        self.output_stream = PygameAudioOutputStream(
            self.audio_channel_assistant_synthesizer
        )
        audio_output_config = speechsdk.audio.AudioOutputConfig(
            stream=speechsdk.audio.PushAudioOutputStream(self.output_stream)
        )
        # audio_output_config.
        speech_config.speech_synthesis_voice_name = voice_name
        self.real_time_speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_output_config
        )

    def _handle_tts_result(
        self,
        tts_result_future: speechsdk.ResultFuture,
        text_to_speak: str,
        file_name: Optional[str] = None,
    ) -> bool:
        """Handle the result of text-to-speech synthesis."""
        if not tts_result_future:
            return False
        speech_synthesis_result = tts_result_future.get()
        if (
            speech_synthesis_result.reason  # type: ignore
            == speechsdk.ResultReason.SynthesizingAudioCompleted
        ):
            logger.info(f"\nSpeech synthesized for text [{text_to_speak}]")
            thread = threading.Thread(target=self.output_stream.handel_tail)
            thread.daemon = True
            thread.start()
            if file_name:
                audio_data_stream = speechsdk.AudioDataStream(speech_synthesis_result)
                audio_data_stream.save_to_wav_file(file_name)
                return True
            return True
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:  # type: ignore
            cancellation_details = speech_synthesis_result.cancellation_details  # type: ignore
            logger.info(f"\nSpeech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    logger.error(
                        f"\nError details: {cancellation_details.error_details}"
                    )
                    logger.warning(
                        "\nDid you set the speech resource key and region values?"
                    )
        else:
            logger.error(
                f"\nspeech_synthesis_result.reason: {speech_synthesis_result.reason}"  # type: ignore
            )
        return False

    def _get_volume_based_on_time(self):
        """Get the volume based on the current time."""
        current_time = time.localtime()
        hour = current_time.tm_hour
        if hour < 8 or hour >= 23:
            return 0.3
        elif 8 <= hour < 12:
            return 0.8
        elif 12 <= hour < 16 or 21 <= hour < 23:
            return 0.5
        else:
            return 0.8

    def _set_volume_imple(self, channel, volume: float, diff_allowed: float = 0.1):
        """Set the volume of a channel if it differs by more than the specified amount."""
        cur_volume = channel.get_volume()
        if abs(cur_volume - volume) > diff_allowed:
            channel.set_volume(volume)

    def _set_volume_based_on_time(self):
        """Set the volume based on the current time."""
        volume = self._get_volume_based_on_time()
        self._set_volume_imple(self.audio_channel_assistant_synthesizer, volume)
        self._set_volume_imple(self.audio_channel_system_prompt, 1)

    def _get_audio_dir(self, session_id: str, message_id: str) -> str:
        """Get the audio directory path for a given message."""
        return f"{self.speaker_config['audio_dir']}/{session_id}/{message_id}"

    def _get_audio_file(
        self, session_id: str, message_id: str, sentence_id: str
    ) -> str:
        """Get the audio file path for a given sentence."""
        return f"{self._get_audio_dir(session_id, message_id)}/{sentence_id}.wav"

    def _create_audio_dir(self, session_id: str, message_id: str):
        """Create the audio directory."""
        audio_dir = self._get_audio_dir(session_id, message_id)
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)

    def remove_audio_dir(self, session_id: str, message_id: str):
        """Remove the audio directory."""
        audio_dir = self._get_audio_dir(session_id, message_id)
        if os.path.exists(audio_dir):
            shutil.rmtree(audio_dir)

    def _create_speech_synthesizer(
        self, voice_name: str, audio_file: str
    ) -> speechsdk.SpeechSynthesizer:
        """Initialize the speech synthesizer."""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.azure_key, region=self.azure_region
        )
        speech_config.speech_synthesis_voice_name = voice_name
        audio_output_config = speechsdk.audio.AudioOutputConfig(filename=audio_file)
        return speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_output_config
        )

    def _create_audio_sound(
        self,
        session_id: str,
        message_id: str,
        sentence_id: str,
        sentence: str,
        voice_name: str,
    ) -> mixer.Sound:
        """Create the audio sound."""
        audio_file = self._get_audio_file(session_id, message_id, sentence_id)
        if not os.path.isfile(audio_file):
            self._create_audio_dir(session_id, message_id)
            synthesizer = self._create_speech_synthesizer(voice_name, audio_file)
            synthesizer.speak_text(sentence)
        sound = mixer.Sound(audio_file)
        return sound

    def _create_audio_queue(
        self,
        session_id: str,
        message_id: str,
        sentence_id_start: str,
        sentence_id_end: str,
        sentences: list[Dict],
        voice_name: str,
    ):
        """Create the audio queue."""
        for sentence_id in range(int(sentence_id_start), int(sentence_id_end) + 1):
            sound = self._create_audio_sound(
                session_id,
                message_id,
                str(sentence_id),
                sentences[sentence_id]["text"],
                voice_name,
            )
            self.audio_queue.append(sound)
        print(f"@:len(self.audio_queue):{len(self.audio_queue)}")

    def pause(self):
        self.audio_channel_assistant_synthesizer.pause()

    def unpause(self):
        self.audio_channel_assistant_synthesizer.unpause()

    def stop(self):
        self.audio_channel_assistant_synthesizer.stop()

    async def _play_response_core(
        self,
        session_id: str,
        message_id: str,
        sentence_id_start: str,
        sentence_id_end: str,
        sentences: list[Dict],
        play_sentence_callback: Callable[[int], Awaitable[None]],
        voice_name: str,
    ):
        """Play the response core."""
        self.audio_channel_assistant_synthesizer.stop()
        self.audio_queue.clear()
        threading.Thread(
            target=self._create_audio_queue,
            args=(
                session_id,
                message_id,
                sentence_id_start,
                sentence_id_end,
                sentences,
                voice_name,
            ),
            daemon=True,
        ).start()
        while len(self.audio_queue) == 0:
            await asyncio.sleep(0.1)
        sentence_id_playing = int(sentence_id_start)
        self.audio_channel_assistant_synthesizer.play(self.audio_queue.popleft())
        await play_sentence_callback(sentence_id_playing)
        had_queue = False
        while self.audio_channel_assistant_synthesizer.get_busy():
            if self.audio_channel_assistant_synthesizer.get_queue():
                had_queue = True
            else:
                if len(self.audio_queue) == 0:
                    if had_queue:
                        had_queue = False
                        sentence_id_playing += 1
                        await play_sentence_callback(sentence_id_playing)
                else:
                    self.audio_channel_assistant_synthesizer.queue(
                        self.audio_queue.popleft()
                    )
                    if had_queue:
                        sentence_id_playing += 1
                        await play_sentence_callback(sentence_id_playing)
            await asyncio.sleep(0.5)
        await play_sentence_callback(-1)  # 播放结束

    async def play_sentence(
        self,
        session_id: str,
        message_id: str,
        sentence_id: str,
        sentences: list[Dict],
        play_sentence_callback: Callable[[int], Awaitable[None]],
        voice_name: str,
    ):
        """Play a sentence in real-time."""
        await self._play_response_core(
            session_id,
            message_id,
            sentence_id,
            sentence_id,
            sentences,
            play_sentence_callback,
            voice_name,
        )

    async def play_sentences(
        self,
        session_id: str,
        message_id: str,
        sentence_id_start: str,
        sentences: list[Dict],
        play_sentence_callback: Callable[[int], Awaitable[None]],
        voice_name: str,
    ):
        """Play a sentence in real-time."""
        await self._play_response_core(
            session_id,
            message_id,
            sentence_id_start,
            str(len(sentences) - 1),
            sentences,
            play_sentence_callback,
            voice_name,
        )

    def speak_text(self, text: str):
        """Speak the given text in real-time."""
        with self.lock:
            self._set_volume_based_on_time()
            result = self.real_time_speech_synthesizer.speak_text_async(text)
            return self._handle_tts_result(result, text)

    def speak_warning(self, text: str):
        """Speak the given warning text in real-time."""
        logger.warning(f"{text}")
        self.speak_text(text)

    def start_speaking_text(self, text: str):
        """Start speaking the given text in real-time."""
        with self.lock:
            self._set_volume_based_on_time()
            result = self.real_time_speech_synthesizer.speak_text_async(text)
            return self._handle_tts_result(result, text)

    def tts(self, text: str) -> bool:
        """Perform text-to-speech synthesis and handle the result."""
        with self.lock:
            self._set_volume_based_on_time()
            result = self.real_time_speech_synthesizer.speak_text_async(text)
            return self._handle_tts_result(result, text)

    async def _play_audio_core(
        self, vfile: str, is_cache: bool, event: Optional[asyncio.Event]
    ):
        """Core logic for playing audio."""
        with self.lock:
            try:
                self._set_volume_based_on_time()
                if not is_cache:
                    sound = mixer.Sound(vfile)
                    self.audio_channel_system_prompt.play(sound)
                    while self.audio_channel_system_prompt.get_busy() and (
                        event is None or not event.is_set()
                    ):
                        await asyncio.sleep(0.1)
                    if event and event.is_set():
                        self.audio_channel_system_prompt.stop()
                else:
                    if vfile not in self.audio_cache:
                        sound = mixer.Sound(vfile)
                        self.audio_cache[vfile] = sound
                    else:
                        sound = self.audio_cache[vfile]
                    self.audio_channel_system_prompt.play(sound)
                    while self.audio_channel_system_prompt.get_busy() and (
                        event is None or not event.is_set()
                    ):
                        await asyncio.sleep(0.1)
                    if event and event.is_set():
                        self.audio_channel_system_prompt.stop()
            except Exception as e:
                logger.exception(f"An error occurred while playing the audio: {e}")

    async def play_audio(
        self, vfile: str, is_cache: bool = False, event: Optional[asyncio.Event] = None
    ):
        """Play audio asynchronously."""
        await self._play_audio_core(vfile, is_cache, event)

    def play_audio_blocking(self, vfile: str, is_cache: bool = False):
        """Blocking call to play audio until playback is complete."""
        if asyncio.get_event_loop().is_running():

            def run_async_play():
                asyncio.run(self.play_audio(vfile, is_cache))

            thread = threading.Thread(target=run_async_play)
            thread.start()
            thread.join()
        else:
            asyncio.run(self.play_audio(vfile, is_cache))

    def play_audio_nonblocking(
        self, vfile: str, is_cache: bool = False
    ) -> threading.Thread:
        """Non-blocking call to play audio in a separate thread."""

        def run_async_play():
            asyncio.run(self.play_audio(vfile, is_cache))
            # if vfile == self.audio_files["start_record"]:
            #     asyncio.run(self.play_audio(vfile, is_cache))

        thread = threading.Thread(target=run_async_play)
        thread.daemon = True
        thread.start()
        return thread

    def play_start_record(self):
        """Play the start record audio."""
        self.play_audio_nonblocking(self.audio_files["start_record"], True)

    def play_end_record(self):
        """Play the end record audio."""
        self.play_audio_nonblocking(self.audio_files["end_record"], True)

    def play_send_message(self):
        """Play the send message audio."""
        self.play_audio_nonblocking(self.audio_files["send_message"], True)

    def play_receive_response(self):
        """Play the receive response audio."""
        self.play_audio_nonblocking(self.audio_files["receive_response"], True)
