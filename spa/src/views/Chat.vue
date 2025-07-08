<template>
    <div class="page-content">
        <!-- 聊天内容区域 - 使用 max-height 限制高度并添加滚动条 -->
        <div class="chat-messages-container">
            <div class="chat-messages" v-for="(msg, text_index) in chatMessages" :key="text_index">
                <MessageBubble :key="text_index" :msg="msg" :show-buttons="true"
                    :showRefreshButton="msg.message_id === max_assistant_message_id"
                    :handleSentenceClick="handleSentenceClick" :update_message="update_message"
                    @delete_audio_files="delete_audio_files" @delete_message="delete_message" @play="play"
                    @pause="pause" @stop="stop" @regenerate="regenerate" />
            </div>
            <div v-show="streaming" class="message_assistant">
                <p v-show="!is_chat_error" v-html="md.render(stream_response)"></p>
                <p v-if="is_chat_error" style="color: red;">{{ stream_response }}</p>
            </div>
            <div style="margin-top: 12px;"></div>
            <div class="message_suggestions" v-for="(suggestion, index) in session_suggestions" :key="index">
                <el-button type="info" plain @click="send_message(suggestion)" style="border-radius: 10px;">
                    {{ suggestion }}
                    <el-icon style="margin-left: 10px;">
                        <Right />
                    </el-icon>
                </el-button>
            </div>
        </div>

        <!-- 输入区域 - 使用固定定位保持在屏幕底部 -->
        <div class="fixed-input-area">
            <div class="input-container">
                <el-input id="input-box" class="input-box" v-model="inputVal" ref="inputRef" type="textarea"
                    placeholder="输入对话内容（Shift + Enter 发送）" @input="handle_input_change"
                    @click="updateCursorPosition(false)" :autosize="{ minRows: 2, maxRows: 9 }"
                    @keydown="handleKeyDown">
                </el-input>
                <div class="button-group">
                    <el-button :icon="MoreFilled" :type="''" text @click="handle_more_click" style="font-size: 24px;" />
                    <el-button :icon="Microphone" :type="is_speech_recognizing ? 'success' : ''" text
                        style="font-size: 24px;" @click="handle_speech_recognize" />
                    <el-button :type="is_input_sendable ? 'primary' : 'info'" :icon="Promotion" circle
                        :disabled="!is_input_sendable" @click="send_user_input" />
                </div>
            </div>
        </div>
    </div>
    <el-drawer header-class="drawer-header" v-model="drawer_visible" :direction="drawer_direction" size="60%">
        <template #header>
            <h4>AI Config</h4>
        </template>
        <template #default>
            <div class="form-container">
                <div v-if="session_ai_config_for_drawer" class="form-wrapper">
                    <el-form :model="session_ai_config_for_drawer" ref="formRef" label-width="200px"
                        class="left-aligned-form">
                        <el-form-item label="Language" prop="language">
                            <el-select v-model="session_ai_config_for_drawer.language" placeholder="请选择语言"
                                @change="session_ai_config_for_drawer.tts_voice = tts_voices[session_ai_config_for_drawer.language][0].ShortName">
                                <el-option v-for="item in languages" :key="item" :label="item" :value="item">
                                </el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="TTS Voice" prop="tts_voice">
                            <el-select v-model="session_ai_config_for_drawer.tts_voice" filterable
                                placeholder="请选择TTS Voice">
                                <el-option v-for="item in tts_voices[session_ai_config_for_drawer.language]"
                                    :key="item.ShortName"
                                    :label="item.LocalName + '——' + item.Gender + '——' + item.LocaleName"
                                    :value="item.ShortName">
                                </el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="Speech Rate" prop="speech_rate">
                            <el-input-number v-model="session_ai_config_for_drawer.speech_rate" :max="2.0" :min="0.5"
                                :step="0.1" placeholder="请输入Speech Rate" />
                        </el-form-item>
                        <el-form-item label="Base URL" prop="base_url">
                            <el-input v-model="session_ai_config_for_drawer.base_url" style="max-width: 600px;"
                                placeholder="请输入Base URL" />
                        </el-form-item>
                        <el-form-item label="API Key" prop="api_key">
                            <el-input v-model="session_ai_config_for_drawer.api_key" style="max-width: 600px;"
                                placeholder="请输入API Key" />
                        </el-form-item>
                        <el-form-item label="Model" prop="model">
                            <el-input v-model="session_ai_config_for_drawer.model" style="max-width: 600px;"
                                placeholder="请输入Model" />
                        </el-form-item>
                        <el-form-item label="Temperature" prop="temperature">
                            <el-input-number v-model="session_ai_config_for_drawer.temperature" :max="2.0" :min="0.0"
                                :step="0.1" placeholder="请输入Temperature" />
                        </el-form-item>
                        <el-form-item label="Max Tokens" prop="max_tokens">
                            <el-input-number v-model="session_ai_config_for_drawer.max_tokens" :max="4096" :min="1"
                                :step="100" placeholder="请输入Max Tokens" />
                        </el-form-item>
                        <el-form-item label="Context Max Tokens" prop="context_max_tokens">
                            <el-input-number v-model="session_ai_config_for_drawer.context_max_tokens" :max="4096"
                                :min="1" :step="100" placeholder="请输入Context Max Tokens" />
                        </el-form-item>
                        <el-form-item label="Max Messages" prop="max_messages">
                            <el-input-number v-model="session_ai_config_for_drawer.max_messages" :max="100" :min="1"
                                :step="1" placeholder="请输入Max Messages" />
                        </el-form-item>
                        <el-form-item label="Auto Play" prop="auto_play">
                            <el-switch v-model="session_ai_config_for_drawer.auto_play" :active-value="true"
                                :inactive-value="false" />
                        </el-form-item>
                        <el-form-item label="Auto Gen Title" prop="auto_gen_title">
                            <el-switch v-model="session_ai_config_for_drawer.auto_gen_title" :active-value="true"
                                :inactive-value="false" />
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </template>
        <template #footer>
            <div style="flex: auto">
                <el-button @click="drawer_visible = false">cancel</el-button>
                <el-button type="primary" @click="update_session_ai_config">confirm</el-button>
            </div>
        </template>
    </el-drawer>
</template>


<script lang="ts" setup>
import { ref, onMounted, watch, watchEffect, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it' // @ts-nocheck
import { Right, MoreFilled, CopyDocument, VideoPlay, VideoPause, Delete, More, Edit, Microphone, Promotion } from '@element-plus/icons-vue'
import type { DrawerProps } from 'element-plus'
import { useWebSocket, WebSocketService } from '@/common/websocket-client'
import { loadJsonFile } from '@/common/json-loader'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor'
import MessageBubble from '@/components/MessageBubble.vue'
import debounce from 'lodash/debounce'

interface Message {
    message_id: number;
    raw_text: string;
    processed_html: string;
    sentences: SentenceInfo[];
    time: string;
    role: string;
    is_playing: boolean;
}
interface AIconfig {
    base_url: string;
    api_key: string;
    model: string;
    temperature: number;
    max_tokens: number;
    context_max_tokens: number;
    max_messages: number;
    language: string;
    tts_voice: string;
    auto_play: boolean;
    auto_gen_title: boolean;
    speech_rate: number;
}
const session_ai_config = ref<AIconfig>()
const session_ai_config_for_drawer = ref<AIconfig>()

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt();
const tts_voices = ref<{ [key: string]: any[] }>({})
const languages = ref<string[]>([])
const drawer_visible = ref(false)
const drawer_direction = ref<DrawerProps['direction']>('ttb')
const chatId = ref('')
const loading = ref(false)
const streaming = ref(false)
const is_chat_error = ref(false)
const stream_response = ref('')
const session_suggestions = ref<string[]>([])
const chatMessages = ref<Message[]>([])
const max_user_message_id = ref(-1)
const max_assistant_message_id = ref(-1)
const sentences = ref<SentenceInfo[]>([])
const inputVal = ref('')
const is_input_sendable = ref(false)
const is_speech_recognizing = ref(false)
const is_stt_changing_input_box = ref(false)
const inputRef = ref(null);
const cursor_position = ref(0);
const text_area_height = ref(0)
let currentWebSocket: WebSocketService | null = null
const currentPlayingSentence = ref({ message_id: -1, sentence_id: -1 })

// 监听路由参数变化，加载新的历史对话
watch(() => route.params.id, (newId) => {
    if (newId !== chatId.value) {
        console.log('newId:', newId)
        loadchatData()
    }
    console.log('@newId:', newId)
})

watchEffect(() => {
    // 直接使用chatMessages，自动追踪依赖
    const userMessages = chatMessages.value.filter(m => m.role === 'user');
    const assistantMessages = chatMessages.value.filter(m => m.role === 'assistant');

    max_user_message_id.value = userMessages.length > 0
        ? Math.max(...userMessages.map(m => m.message_id))
        : -1;

    max_assistant_message_id.value = assistantMessages.length > 0
        ? Math.max(...assistantMessages.map(m => m.message_id))
        : -1;
});

onMounted(async () => {
    loadchatData()
    tts_voices.value = await loadJsonFile('/tts_voices.json')
    languages.value = Object.keys(tts_voices.value)
    const textarea = document.querySelector('#input-box') as HTMLTextAreaElement;
    text_area_height.value = textarea.clientHeight
    document.documentElement.style.setProperty('--fixed-input-area-padding-top', textarea.clientHeight + 'px');
})

const update_input_sendable = () => {
    is_input_sendable.value = inputVal.value.trim() != ""
}

// 实时更新光标位置
const updateCursorPosition = (is_input_change_event: boolean = false) => {
    update_input_sendable()
    setTimeout(() => {
        if (inputRef.value) {
            const textarea = inputRef.value.$refs.textarea; // @ts-ignore
            if (textarea) {
                cursor_position.value = textarea.selectionStart;
                console.log('cursor_position.value:', cursor_position.value)
                console.log('is_input_change_event:', is_input_change_event)
                if (!is_stt_changing_input_box.value && is_speech_recognizing.value) {
                    // if (is_speech_recognizing.value) {
                    const msg = {
                        "type": "update_cursor_position",
                        "data": {
                            "original_text": inputVal.value,
                            "cursor_position": cursor_position.value,
                        },
                    }
                    currentWebSocket?.send(msg)
                }
            }
        }
    }, 100);
};


// 设置光标位置
const set_cursor_position = (position: number) => {
    nextTick(() => {
        if (inputRef.value) {
            const textarea = inputRef.value.$refs.textarea; // @ts-ignore

            if (textarea) {
                // 限制位置范围

                const validPosition = Math.max(0, Math.min(position, inputVal.value.length));

                // 设置光标位置
                textarea.focus();
                textarea.setSelectionRange(validPosition, validPosition);

                // 更新显示
                cursor_position.value = validPosition;
                // targetPosition.value = validPosition;

                // 触发输入事件使Element UI组件同步状态
                const event = new Event('input', { bubbles: true });
                textarea.dispatchEvent(event);
            }
        }
    });
};


const handle_input_change = () => {
    updateCursorPosition(true)
}

const handle_speech_recognize = () => {
    if (is_speech_recognizing.value) {
        stop_speech_recognize()
    } else {
        start_speech_recognize()
    }
}

const start_speech_recognize = () => {
    if (currentWebSocket) {
        if (session_ai_config.value) {
            let language = session_ai_config.value.language
            switch (language) {
                case "日本語":
                    language = "ja-JP"
                    break;
                case "中文":
                    language = "zh-CN"
                    break;
                case "English":
                    language = "en-US"
                    break;
                default:
                    language = "zh-CN"
                    break;
            }
            const msg = {
                "type": "start_speech_recognize",
                "data": {
                    "input_text": inputVal.value,
                    "cursor_position": cursor_position.value,
                    "language": language,
                },
            }
            console.log(msg)
            currentWebSocket.send(msg)
        }
    }
}

const stop_speech_recognize = () => {
    if (currentWebSocket) {
        currentWebSocket.send({
            "type": "stop_speech_recognize",
            "data": {},
        })
    }
}

const handle_more_click = () => {
    drawer_visible.value = true
    session_ai_config_for_drawer.value = JSON.parse(JSON.stringify(session_ai_config.value))
}

const get_session_id = () => {
    return route.params.id
}

const update_session_ai_config = () => {
    const session_id = get_session_id()
    const msg = {
        "type": "update_session_ai_config",
        "data": {
            "session_id": session_id,
            "ai_config": session_ai_config_for_drawer.value,
        },
    }
    currentWebSocket?.send(msg)
    drawer_visible.value = false
}

const update_message = (message_id: number, raw_text: string) => {
    if (message_id === max_user_message_id.value) {
        if (max_assistant_message_id.value > max_user_message_id.value) {
            delete_message(max_assistant_message_id.value)
        }
        delete_message(max_user_message_id.value)
        // make sure the message is deleted before sending the new message
        setTimeout(() => {
            send_message(raw_text)
        }, 100)
    } else {
        const session_id = get_session_id()
        const result = processMarkdown(raw_text, message_id)
        const msg = {
            "type": "update_message",
            "data": {
                "session_id": session_id,
                "message_id": message_id,
                "raw_text": raw_text,
                "sentences": result.sentences,
            },
        }
        currentWebSocket?.send(msg)
    }
}

const regenerate = () => {
    let last_user_input = ""
    const msg = chatMessages.value.find(msg => msg.message_id === max_user_message_id.value)
    if (msg) {
        last_user_input = msg.raw_text
    }
    if (last_user_input) {
        delete_message(max_assistant_message_id.value)
        delete_message(max_user_message_id.value)
        // make sure the message is deleted before sending the new message
        setTimeout(() => {
            send_message(last_user_input)
        }, 100)
    }
}

const delete_audio_files = (message_id: number) => {
    const session_id = get_session_id()
    const msg = {
        "type": "delete_audio_files",
        "data": {
            "session_id": session_id,
            "message_id": message_id,
        },
    }
    currentWebSocket?.send(msg)
}

const generate_audio_files = (message_id: number, sentence_id_start: number, sentence_id_end: number) => {
    if (!session_ai_config.value) {
        return
    }
    const session_id = get_session_id()
    const voice_name = session_ai_config.value.tts_voice
    const msg = {
        "type": "generate_audio_files",
        "data": {
            "session_id": session_id,
            "message_id": message_id,
            "sentence_id_start": sentence_id_start,
            "sentence_id_end": sentence_id_end,
            "voice_name": voice_name,
        },
    }
    currentWebSocket?.send(msg)
}

const delete_message = (message_id: number) => {
    const session_id = get_session_id()
    const msg = {
        "type": "delete_message",
        "data": {
            "session_id": session_id,
            "message_id": message_id,
        },
    }
    currentWebSocket?.send(msg)
}

const handleInput = () => {
    const textarea = document.querySelector('#input-box') as HTMLTextAreaElement;
    if (textarea) {
        if (text_area_height.value !== textarea.clientHeight) {
            document.documentElement.style.setProperty('--fixed-input-area-padding-top', textarea.clientHeight + 'px');
            const scrollContainer =
                document.documentElement.scrollTop > 0
                    ? document.documentElement
                    : document.body;
            const scroll_top = textarea.clientHeight - text_area_height.value
            scrollContainer.scrollBy({
                top: scroll_top,
                behavior: "instant"
            });
            text_area_height.value = textarea.clientHeight
        }
    }
};

watch(inputVal, (newVal) => {
    setTimeout(() => {
        handleInput()
    }, 100)
})


// 添加样式类来高亮显示正在播放的句子
const highlightPlayingSentence = () => {
    // 移除之前高亮的句子
    const previousHighlighted = document.querySelector('.sentence-playing')
    if (previousHighlighted) {
        previousHighlighted.classList.remove('sentence-playing')
    }

    // 如果sentence_id为-1，表示播放完毕，不需要高亮任何句子
    if (currentPlayingSentence.value.sentence_id === -1) {
        return
    }

    // 高亮当前播放的句子
    const selector = `.content[data-param1="${currentPlayingSentence.value.message_id}"][data-param2="${currentPlayingSentence.value.sentence_id}"]`
    const element = document.querySelector(selector)
    if (element) {
        element.classList.add('sentence-playing')
        // 滚动到高亮的句子
        // element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
}

// 监听当前播放句子的变化，更新高亮
watch(currentPlayingSentence, highlightPlayingSentence)

const scrollToBottom = () => {
    const scrollContainer =
        document.documentElement.scrollTop > 0
            ? document.documentElement
            : document.body;
    scrollContainer.scrollTop = scrollContainer.scrollHeight
}

const scrollToBottomDebounced = debounce(scrollToBottom, 200)

// 加载历史对话数据
const loadchatData = async () => {
    try {
        chatId.value = route.params.id as string
        loading.value = true

        // 关闭当前WebSocket连接（如果有）
        if (currentWebSocket) {
            currentWebSocket.close()
        }

        // 清空当前消息
        chatMessages.value = []
        session_suggestions.value = []

        // 初始化WebSocket连接
        const wsUrl = `ws://localhost:4999/ws/aichat/${chatId.value}`
        console.log('Connecting to:', wsUrl)

        currentWebSocket = useWebSocket(wsUrl)
        currentWebSocket.handleMessage = (message: any) => {
            // console.log('receive message:', message)

            switch (message.type) {
                case 'parse_request':
                    console.log('收到用户消息:', message.data.data)
                    switch (message.data.type) {
                        case 'user_message':
                            {
                                const messageId = message.data.data.message_id
                                const user_message = message.data.data.user_message
                                console.log("user_message:", user_message, messageId)
                                const result = processMarkdown(user_message, messageId)
                                chatMessages.value.push({
                                    message_id: messageId,
                                    raw_text: user_message,
                                    processed_html: result.html,
                                    sentences: result.sentences,
                                    time: format_time_now(),
                                    role: "user",
                                    is_playing: false,
                                })
                                const msg = {
                                    type: 'parsed_response',
                                    data: {
                                        type: 'user_message',
                                        data: {
                                            message_id: messageId,
                                            user_message: user_message,
                                            sentences: result.sentences,
                                        },
                                    },
                                }
                                currentWebSocket?.send(msg)
                            }
                            break
                        case "ai_response":
                            {
                                const messageId = message.data.data.message_id
                                const response = message.data.data.response
                                const result = processMarkdown(response, messageId)
                                console.log("ai_response:", response, messageId)
                                chatMessages.value.push({
                                    message_id: messageId,
                                    raw_text: response,
                                    processed_html: result.html,
                                    sentences: result.sentences,
                                    time: format_time_now(),
                                    role: "assistant",
                                    is_playing: false,
                                })
                                const msg = {
                                    type: 'parsed_response',
                                    data: {
                                        type: 'ai_response',
                                        data: {
                                            message_id: messageId,
                                            response: response,
                                            sentences: result.sentences,
                                        },
                                    },
                                }
                                currentWebSocket?.send(msg)
                                scrollToBottomDebounced()

                                if (session_ai_config.value && session_ai_config.value.auto_play) {
                                    setTimeout(() => {
                                        if (result.sentences.length >= 2) {
                                            generate_audio_files(messageId, 0, 0)
                                        }
                                        play(messageId)
                                    }, 1000)
                                }
                            }
                            break;
                        default:
                            console.log('未知消息类型 for parse_request:', message)
                    }
                    break;
                case "stream_response":
                    {
                        streaming.value = message.data.is_streaming
                        is_chat_error.value = message.data.is_chat_error
                        stream_response.value = message.data.response
                        scrollToBottom()
                    }
                    break
                case 'session_suggestions':
                    {
                        session_suggestions.value = message.data.suggestions
                    }
                    break
                case 'speech_recognizing':
                    {
                        is_speech_recognizing.value = true
                        const stt_text = message.data.stt_text
                        const cursor_position = message.data.cursor_position
                        console.log("stt_text:", stt_text)
                        is_stt_changing_input_box.value = true
                        inputVal.value = stt_text
                        set_cursor_position(cursor_position)
                        is_stt_changing_input_box.value = false
                        update_input_sendable()
                        // handle_input_change()
                    }
                    break
                case 'stop_speech_recognize':
                    {
                        is_speech_recognizing.value = false
                    }
                    break
                case 'the_sentence_playing':
                    {
                        const message_id = message.data.message_id
                        const sentence_id = message.data.sentence_id
                        const msg = chatMessages.value.find(msg => msg.message_id === message_id)
                        if (msg) {
                            msg.is_playing = sentence_id !== -1
                        }
                        console.log("the_sentence_playing:", message_id, sentence_id)
                        currentPlayingSentence.value = { message_id, sentence_id }
                    }
                    break
                case 'update_message':
                    {
                        const message_id = message.data.message_id
                        const raw_text = message.data.raw_text
                        const msg = chatMessages.value.find(msg => msg.message_id === message_id)
                        console.log("update_message:", message_id, raw_text)
                        if (msg) {
                            const result = processMarkdown(raw_text, message_id)
                            msg.raw_text = raw_text
                            msg.sentences = result.sentences
                            msg.processed_html = result.html
                        }
                    }
                    break
                case 'delete_message':
                    {
                        const message_id = message.data.message_id
                        const index = chatMessages.value.findIndex(msg => msg.message_id === message_id)
                        if (index !== -1) {
                            chatMessages.value.splice(index, 1)
                        }
                    }
                    break
                case 'session_messages':
                    chatMessages.value = []
                    const messages = message.data.messages
                    messages.forEach((msg: any) => {
                        const message_id = msg.id
                        const raw_message = msg.raw_text
                        const result = processMarkdown(raw_message, message_id)
                        chatMessages.value.push({
                            message_id: message_id,
                            raw_text: raw_message,
                            processed_html: result.html,
                            sentences: result.sentences,
                            time: msg.timestamp,
                            role: msg.role,
                            is_playing: false,
                        })
                    })
                    scrollToBottomDebounced()
                    break
                case 'session_ai_config':
                    {
                        const ai_config = message.data.ai_config
                        //如果如果session_ai_config的某些key不存在与ai_config，给ai_config填入默认值
                        if (ai_config.language == undefined)
                            ai_config.language = "中文"
                        session_ai_config.value = ai_config
                        session_suggestions.value = ai_config.suggestions
                        console.log("session_ai_config:", session_ai_config.value)
                    }
                    break
                case 'error_session_not_exist':
                    {
                        console.log("session_id:", message.data.session_id, " not exist")
                        router.push({ name: 'Home' })
                        currentWebSocket?.close()
                    }
                    break
                default:
                    console.log('未知消息类型:', message)
            }
        }

        // 模拟数据加载延迟
        await new Promise(resolve => setTimeout(resolve, 500))

    } catch (error) {
        console.error('加载历史对话失败:', error)
        // 可以显示错误提示
    } finally {
        loading.value = false
    }
}

const send_user_input = () => {
    if (!is_input_sendable.value) return
    send_message(inputVal.value)
    inputVal.value = ''
    update_input_sendable()
}

// 发送消息方法
const send_message = (user_input: string) => {
    session_suggestions.value = []
    if (!session_ai_config.value) {
        return
    }
    if (is_speech_recognizing.value) {
        stop_speech_recognize()
    }
    const message = {
        type: 'user_input',
        data: {
            user_message: user_input,
            session_id: get_session_id(),
            auto_gen_title: session_ai_config.value.auto_gen_title,
        },
    }
    currentWebSocket?.send(message)
    scrollToBottom()
}

// 格式化时间
const format_time_now = () => {
    const time = new Date()
    return (
        time.getFullYear() + '-' +
        (time.getMonth() + 1).toString().padStart(2, '0') + '-' +
        time.getDate().toString().padStart(2, '0') + ' ' +
        time.getHours().toString().padStart(2, '0') + ':' +
        time.getMinutes().toString().padStart(2, '0') + ':' +
        time.getSeconds().toString().padStart(2, '0')
    )
}

// 语音控制方法
const pause = () => {
    currentWebSocket?.send({
        type: 'pause',
        data: {},
    })
}

const play = (message_id: number) => {
    if (!session_ai_config.value) {
        return
    }
    const msg = {
        type: 'play',
        data: {
            message_id: message_id,
            voice_name: session_ai_config.value.tts_voice,
        },
    }
    currentWebSocket?.send(msg)
}

const stop = () => {
    currentWebSocket?.send({
        type: 'stop',
        data: {},
    })
}

// 句子点击处理
const handleSentenceClick = (e: MouseEvent) => {
    const isOptionPressed = e.altKey
    const isCommandPressed = e.metaKey // macOS 上的 Command 键
    const isCtrlPressed = e.ctrlKey

    if (isOptionPressed) {
        const target = e.target as HTMLElement
        const contentElement = target.closest('.content')

        if (contentElement && (contentElement as HTMLElement).dataset && session_ai_config.value) {
            const messageId = (contentElement as HTMLElement).dataset.param1
            const sentenceId = (contentElement as HTMLElement).dataset.param2

            const sentence = sentences.value.find(
                s => s.messageId.toString() === messageId && s.sentenceId.toString() === sentenceId
            )

            if (sentence) {
                console.log('点击的句子:', sentence)
            }
            const type = !isCommandPressed ? 'play_the_sentence' : 'play_sentences'
            const message = {
                type: type,
                data: {
                    message_id: Number(messageId),
                    sentence_id: Number(sentenceId),
                    voice_name: session_ai_config.value.tts_voice,
                }
            }

            currentWebSocket?.send(message)
        }
    }
}

// 处理输入框按键事件
const handleKeyDown = (e: KeyboardEvent) => {
    // if (is_speech_recognizing.value) {
    //     stop_speech_recognize()
    // }
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Tab'].includes(e.key)) {
        updateCursorPosition(false)
    }
    // 检查 Alt/Option 键和 Command 键是否同时按下
    if (e.altKey && e.metaKey) {
        e.preventDefault()
        handle_speech_recognize()
    }
    if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault()
        send_user_input()
    }
}

</script>

<style scoped>
:root {
    --fixed-input-area-padding-top: 100px;
}

.page-content {
    padding-bottom: 1px;
}

.chat-messages-container {
    margin-bottom: calc(var(--fixed-input-area-padding-top) + 100px);
}

.message_assistant {
    padding: 8px 12px;
    border-radius: 8px;
    color: #333333;
    background-blend-mode: luminosity;

    max-width: clamp(300px, 80vw, 800px);
    font-size: 16px;
    line-height: 1.6;
    padding: 20px;
    margin: 0 auto;
    text-align: left;
    background-color: #f5f0e6;
}

.message_suggestions {
    padding: 8px 0px;
    border-radius: 8px;
    color: #333333;
    background-blend-mode: luminosity;
    max-width: clamp(300px, 80vw, 800px);
    font-size: 16px;
    line-height: 1.6;
    margin: 0 auto;
    text-align: left;
}

.fixed-input-area {
    position: fixed;
    bottom: 0px;
    padding-top: var(--fixed-input-area-padding-top);
    z-index: 100;
    left: calc(var(--main-content-left-margin) + 1px);
    right: 0;
    background-color: var(--el-bg-color);
}

.input-container {
    margin: 0 auto;
    max-width: clamp(300px, 80vw, 800px);
}

.button-group {
    padding: 5px 5px 20px 5px;
    display: flex;
    justify-content: flex-end;
}

.form-container {
    display: flex;
    justify-content: center;
    /* 水平居中 */
    padding: 20px;
}

.form-wrapper {
    width: 100%;
    max-width: 40vw;
    /* 限制表单最大宽度 */
}

/* 如果需要表单项左对齐排列，可以添加以下样式 */
.el-form-item {
    justify-content: flex-start;
    /* 确保表单项左对齐 */
}
</style>
