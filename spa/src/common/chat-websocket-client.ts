import { WebSocketService } from '@/common/websocket-client'

class ChatWebSocketService extends WebSocketService {
    constructor(url: string) {
        super(url)
    }

    private _send(type: string, data: {} | null = null) {
        this.send({
            type: type,
            data: {
                ...data,
            },
        })
    }

    private _sendWithMessageId(type: string, messageId: number, data: {} | null = null) {
        this._send(type, {
            message_id: messageId,
            ...data,
        })
    }

    // 发送用户输入
    sendUserInput(message: string) {
        this._send(
            'user_input',
            {
                user_message: message,
            }
        )
    }

    // 发送解析响应
    sendParsedUserMessage(messageId: number, sentences: any[]) {
        this._sendWithMessageId('parsed_user_message', messageId, {
            sentences: sentences
        })
    }

    sendParsedAiResponse(messageId: number, sentences: any[]) {
        this._sendWithMessageId('parsed_ai_response', messageId, {
            sentences: sentences
        })
    }

    // 语音识别控制
    sendStartSpeechRecognition(text: string, cursorPos: number, lang: string) {
        this._send('start_speech_recognize', {
            input_text: text,
            cursor_position: cursorPos,
            language: lang,
        })
    }

    sendStopSpeechRecognition() {
        this._send('stop_speech_recognize')
    }

    // 消息控制
    sendDeleteAudioFiles(messageId: number) {
        this._sendWithMessageId('delete_audio_files', messageId)
    }

    sendUpdateMessage(messageId: number, rawText: string, sentences: any[]) {
        this._sendWithMessageId('update_message', messageId, {
            raw_text: rawText,
            sentences: sentences,
        })
    }

    sendDeleteMessage(messageId: number) {
        this._sendWithMessageId('delete_message', messageId)
    }

    sendUpdateSessionConfig(config: any) {
        this._send('update_session_ai_config', { ai_config: config })
    }

    // 播放控制
    sendGenerateAudioFiles(messageId: number, sentenceIdStart: number, sentenceIdEnd: number) {
        this._sendWithMessageId('generate_audio_files', messageId, {
            sentence_id_start: sentenceIdStart,
            sentence_id_end: sentenceIdEnd,
        })
    }

    sendPlayMessage(messageId: number) {
        this._sendWithMessageId('play', messageId)
    }

    sendPlayTheSentence(messageId: number, sentenceId: number) {
        this._sendWithMessageId('play_the_sentence', messageId, {
            sentence_id: sentenceId,
        })
    }

    sendPlaySentences(messageId: number, sentenceId: number) {
        this._sendWithMessageId('play_sentences', messageId, {
            sentence_id: sentenceId,
        })
    }

    sendPausePlayback() {
        this._send('pause')
    }

    sendStopPlayback() {
        this._send('stop')
    }

}

// 导出单例或工厂函数，根据项目需求选择
let chatWebSocketInstance: ChatWebSocketService | null = null;
export function useChatWebSocket(chatId: number) {
    chatWebSocketInstance = new ChatWebSocketService("ws://localhost:4999/ws/aichat/" + chatId);
    return chatWebSocketInstance;
}
export { ChatWebSocketService }
