<template>
    <div class="page-content">
        <!-- 聊天内容区域 - 使用 max-height 限制高度并添加滚动条 -->
        <div class="chat-messages-container">
            <div class="chat-messages" v-for="(msg, text_id) in chatMessages" :key="text_id">
                <div class="message" :class="{ 'self': msg.isSelf }">
                    <div class="markdown-container" @click="handleSentenceClick">
                        <p v-html="msg.processed_html"></p>
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
        <div class="fixed-input-area">
            <el-input v-model="inputVal" type="textarea" placeholder="输入对话内容（Shift + Enter 发送）"
                :autosize="{ minRows: 5, maxRows: 9 }" @keydown="handleKeyDown" />
            <el-button type="primary" @click="sendMessage">发送</el-button>
        </div>
    </div>
</template>


<script lang="ts" setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { useWebSocket, WebSocketService } from '@/common/websocket-client'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor'
import debounce from 'lodash/debounce'

interface Message {
    processed_html: string;
    sentences: SentenceInfo[];
    time: string;
    isSelf: boolean;
}

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt();
const historyId = ref('')
const loading = ref(false)
const streaming = ref(false)
const stream_response = ref('This is a test.')
const chatMessages = ref<Message[]>([])
const sentences = ref<SentenceInfo[]>([])
const inputVal = ref('')
let currentWebSocket: WebSocketService | null = null

onMounted(() => {
    loadHistoryData()
})

// 监听路由参数变化，加载新的历史对话
watch(() => route.params.id, (newId) => {
    if (newId !== historyId.value) {
        console.log('newId:', newId)
        loadHistoryData()
    }
    console.log('@newId:', newId)
})

const scrollToBottom = () => {
    const scrollContainer = document.querySelector('.chat-messages-container') as HTMLElement
    scrollContainer.scrollTop = scrollContainer.scrollHeight
}

const scrollToBottomDebounced = debounce(scrollToBottom, 200)
// {
//                         nextTick(() => {
//                         setTimeout(() => {
//                             const container = document.querySelector('.chat-messages-container')
//                             if (container) container.scrollTop = container.scrollHeight
//                         }, 1000) // 100ms 的延迟，时间可根据实际情况调整
//                     })
// }

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
/* 聊天内容容器 */
.chat-messages-container {
    height: calc(100vh - 11em);
    /* 留出输入区域的空间 */
    overflow-y: auto;
    padding: 20px;
    box-sizing: border-box;
}

/* 固定在底部的输入区域 */
.fixed-input-area {
    position: fixed;
    bottom: 0;
    left: 30vw;
    right: 10vw;
    padding: 20px;
    /* background-color: white; 根据需要调整背景色 */
    /* border-top: 1px solid #eee; */
    /* box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1); */
    z-index: 100;
    /* 确保在最上层 */
    display: flex;
    gap: 10px;
    align-items: flex-end;
}

/* 聊天消息样式优化 */
.message {
    max-width: 60%;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    color: #000;
}

.message.self {
    text-align: left;
    background-color: #d3eafd;
    margin-left: auto;
    margin-bottom: 12px;
    margin-top: 12px;
}

.message:not(.self) {
    /* 关键：通过 margin 自动居中，需配合 max-width 限制宽度 */
    margin: 0 auto;
    text-align: left;
    background-color: #f1f1f1;
    /* 保留 max-width 让内容不会过宽，也可根据需求调整数值 */
    max-width: 60%;
}

.content {
    margin-bottom: 4px;
}

.time {
    font-size: 12px;
    color: #666;
    text-align: right;
}
</style>
