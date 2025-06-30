<template>
    <div class="page-content">
        <!-- 聊天内容区域 - 使用 max-height 限制高度并添加滚动条 -->
        <div class="chat-messages-container">
            <div class="chat-messages" v-for="(msg, text_id) in chatMessages" :key="text_id">
                <div class="message" :class="{ 'self': msg.isSelf }">
                    <div class="markdown-container" @click="handleSentenceClick">
                        <p v-html="msg.processed_html"></p>
                        <!-- <p>{{ msg.processed_html }}</p> -->
                    </div>
                    <el-button type="primary" @click="unpause">播放</el-button>
                    <el-button type="primary" @click="pause">暂停</el-button>
                    <el-button type="primary" @click="stop">停止</el-button>

                    <div class="time">{{ msg.time }}</div>
                </div>
            </div>
            <div v-if="streaming">
                <div class="message not(self)">
                    <div class="markdown-container">
                        <p v-html="md.render(stream_response)"></p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 输入区域 - 使用固定定位保持在屏幕底部 -->
        <div class="fixed-input-area" :style="{
            boxShadow: `var(--el-box-shadow-light)`,
        }">
            <div class="input-container">
                <el-input v-model="inputVal" type="textarea" placeholder="输入对话内容（Shift + Enter 发送）"
                    :autosize="{ minRows: 2, maxRows: 9 }" @keydown="handleKeyDown">
                </el-input>
                <div class="button-group">
                    <!-- copy session_ai_config to session_ai_config_for_drawer -->
                    <el-button :icon="MoreFilled" :type="''" text @click="handle_more_click" style="font-size: 24px;" />
                    <el-button :icon="Microphone" :type="''" text style="font-size: 24px;" />
                    <el-button type="primary" :icon="Promotion" circle />
                </div>
            </div>
        </div>
    </div>
    <el-drawer v-model="drawer_visible" :direction="drawer_direction" size="70%">
        <template #header>
            <h4>AI Config</h4>
        </template>
        <template #default>
            <div class="form-container">
                <div class="form-wrapper">
                    <el-form :model="session_ai_config_for_drawer" ref="formRef" label-width="120px"
                        class="left-aligned-form">
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
                            <el-input-number v-model="session_ai_config_for_drawer.temperature" max="2" min="0"
                                step="0.1" placeholder="请输入Temperature" />
                        </el-form-item>
                        <el-form-item label="Max Tokens" prop="max_tokens">
                            <el-input-number v-model="session_ai_config_for_drawer.max_tokens" max="4096" min="1"
                                step="100" placeholder="请输入Max Tokens" />
                        </el-form-item>
                        <el-form-item label="Context Max Tokens" prop="context_max_tokens">
                            <el-input-number v-model="session_ai_config_for_drawer.context_max_tokens" max="4096"
                                min="1" step="100" placeholder="请输入Context Max Tokens" />
                        </el-form-item>
                        <el-form-item label="Max Messages" prop="max_messages">
                            <el-input-number v-model="session_ai_config_for_drawer.max_messages" max="100" min="1"
                                step="1" placeholder="请输入Max Messages" />
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </template>
        <template #footer>
            <div style="flex: auto">
                <el-button @click="drawer_visible = false">cancel</el-button>
                <el-button type="primary" @click="drawer_visible = false">confirm</el-button>
            </div>
        </template>
    </el-drawer>
</template>


<script lang="ts" setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { Refresh, MoreFilled, Delete, More, EditPen, ArrowLeft, ArrowRight, Microphone, Setting, Promotion } from '@element-plus/icons-vue'
import type { DrawerProps } from 'element-plus'
import { useWebSocket, WebSocketService } from '@/common/websocket-client'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor'
import debounce from 'lodash/debounce'

interface Message {
    processed_html: string;
    sentences: SentenceInfo[];
    time: string;
    isSelf: boolean;
}
interface AIconfig {
    base_url: string;
    api_key: string;
    model: string;
    temperature: number;
    max_tokens: number;
    context_max_tokens: number;
    max_messages: number;
}
const session_ai_config = ref<AIconfig>()
const session_ai_config_for_drawer = ref<AIconfig>()

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt();
const drawer_visible = ref(false)
const drawer_direction = ref<DrawerProps['direction']>('ttb')
const historyId = ref('')
const loading = ref(false)
const streaming = ref(false)
const stream_response = ref('This is a test.')
const chatMessages = ref<Message[]>([])
const sentences = ref<SentenceInfo[]>([])
const inputVal = ref('')
const text_area_height = ref(0)
let currentWebSocket: WebSocketService | null = null
const currentPlayingSentence = ref({ message_id: -1, sentence_id: -1 })

// 监听路由参数变化，加载新的历史对话
watch(() => route.params.id, (newId) => {
    if (newId !== historyId.value) {
        console.log('newId:', newId)
        loadHistoryData()
    }
    console.log('@newId:', newId)
})

onMounted(() => {
    loadHistoryData()
    const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
    text_area_height.value = textarea.clientHeight
    document.documentElement.style.setProperty('--fixed-input-area-padding-top', textarea.clientHeight + 'px');
})

const handle_more_click = () => {
    drawer_visible.value = true
    session_ai_config_for_drawer.value = JSON.parse(JSON.stringify(session_ai_config.value))
}

const handleInput = () => {
    const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
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
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
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
const loadHistoryData = async () => {
    try {
        historyId.value = route.params.id as string
        loading.value = true

        // 关闭当前WebSocket连接（如果有）
        if (currentWebSocket) {
            currentWebSocket.close()
        }

        // 清空当前消息
        chatMessages.value = []

        // 这里可以从API加载历史对话数据
        // 示例：const response = await fetchHistoryData(historyId.value)
        // chatMessages.value = response.data

        // 初始化WebSocket连接
        const wsUrl = `ws://localhost:4999/ws/aichat/${historyId.value}`
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
                                    processed_html: result.html,
                                    sentences: result.sentences,
                                    time: format_time_now(),
                                    isSelf: true,
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
                                    processed_html: result.html,
                                    sentences: result.sentences,
                                    time: format_time_now(),
                                    isSelf: false,
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
                            }
                            break;
                        default:
                            console.log('未知消息类型 for parse_request:', message)
                    }
                    break;
                case "stream_response":
                    {
                        streaming.value = message.data.is_streaming
                        stream_response.value = message.data.response
                        scrollToBottom()
                    }
                    break
                case 'the_sentence_playing':
                    {
                        const message_id = message.data.message_id
                        const sentence_id = message.data.sentence_id
                        console.log("the_sentence_playing:", message_id, sentence_id)
                        currentPlayingSentence.value = { message_id, sentence_id }
                    }
                    break
                case 'session_messages':
                    chatMessages.value = []
                    const messages = message.data
                    messages.forEach((msg: any) => {
                        const message_id = msg[0]
                        const raw_message = msg[2]
                        const result = processMarkdown(raw_message, message_id)
                        chatMessages.value.push({
                            processed_html: result.html,
                            sentences: result.sentences,
                            time: msg[4],
                            isSelf: msg[1] != "assistant",
                        })
                    })
                    scrollToBottomDebounced()
                    break
                case 'session_ai_config':
                    {
                        const ai_config = message.data
                        session_ai_config.value = ai_config
                        console.log("session_ai_config:", session_ai_config.value)
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

// 发送消息方法
const sendMessage = () => {
    if (!inputVal.value.trim()) return

    const message = {
        type: 'user_input',
        data: {
            user_message: inputVal.value,
            session_id: historyId.value,
        },
    }
    currentWebSocket?.send(message)
    inputVal.value = ''

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

const unpause = () => {
    currentWebSocket?.send({
        type: 'unpause',
        data: {},
    })
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

    if (isOptionPressed || isCommandPressed) {
        const target = e.target as HTMLElement
        const contentElement = target.closest('.content')

        if (contentElement) {
            const messageId = contentElement.dataset.param1
            const sentenceId = contentElement.dataset.param2

            const sentence = sentences.value.find(
                s => s.messageId.toString() === messageId && s.sentenceId.toString() === sentenceId
            )

            if (sentence) {
                console.log('点击的句子:', sentence)
            }
            const type = isCommandPressed ? 'play_the_sentence' : 'play_sentences'
            const message = {
                type: type,
                data: {
                    message_id: Number(messageId),
                    sentence_id: Number(sentenceId),
                }
            }

            currentWebSocket?.send(message)
        }
    }
}

// 处理输入框按键事件
const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault()
        sendMessage()
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


.fixed-input-area {
    position: fixed;
    bottom: 0px;
    /* padding-top: 100px; */
    padding-top: var(--fixed-input-area-padding-top);
    z-index: 100;
    left: calc(var(--main-content-left-margin) + 10px);
    right: 0;
    background-color: var(--el-bg-color);
}

.input-container {
    margin: 0 auto;
    max-width: clamp(300px, 80vw, 800px);
    font-size: 16px;
    line-height: 1.6;
}

.button-group {
    padding: 5px 5px 20px 5px;
    display: flex;
    justify-content: flex-end;
}

/* 聊天消息样式优化 */
.message {
    /* flex: 1; */
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    color: #000;
}

.message.self {
    max-width: 60%;
    text-align: left;
    background-color: #d3eafd;
    /* margin: 0 auto; */
    margin-left: auto;
    margin-bottom: 12px;
    margin-top: 12px;
    padding: 20px;
    /* margin-right: 10px; */
}

.message:not(.self) {
    max-width: clamp(300px, 80vw, 800px);
    font-size: 16px;
    line-height: 1.6;
    padding: 20px;
    margin: 0 auto;
    text-align: left;
    /* background-color: #f1f1f1; */
    width: 960px;

    background-color: #f5f0e6;
    color: #333333;
    background-blend-mode: luminosity;
    filter: brightness(90%);

}

/* 基础护眼背景 */
.fatigue-reducing-bg {
    background-color: #f5f0e6;
    /* 米白色 */
    color: #333333;
    /* 深灰色文字 */
    /* 动态亮度调节 */
    background-blend-mode: luminosity;
    filter: brightness(90%);
}

/* 夜间模式 */
.night-mode {
    background-color: #222222;
    /* 深灰色 */
    color: #e0e0e0;
    /* 浅灰色文字 */
    /* 降低对比度至7:1 */
    mix-blend-mode: difference;
}

.content {
    margin-bottom: 4px;
}

.time {
    font-size: 12px;
    color: #666;
    text-align: right;
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
