<template>
    <div class="page-content">
        <!-- 聊天消息区域 -->
        <div class="chat-container">
            <!-- 只有当 webSocket 不为 null 时才渲染 ChatMessages 组件 -->
            <ChatMessages v-if="webSocket !== null" :websocket="webSocket" :messages="chatMessages"
                @send-message="sendMessage" @scroll-up="isScrolledWhenStreaming = true" />
            <div v-if="isSentNoStream" class="loader-container">
                <ThreeDotsLoader class="threeDotsLoader" />
            </div>
            <!-- 流式响应展示 -->
            <MessageStream :streaming="streaming" :error="isChatError" :content="streamResponse" />
            <!-- 建议消息列表 -->
            <SuggestionsList :suggestions="sessionSuggestions" @send="sendMessage" />
        </div>

        <!-- 输入区域 -->
        <ChatInput v-if="webSocket !== null" :webSocket="webSocket" :language="sessionAiConfig?.language"
            :isSpeechRecognizing="isSpeechRecognizing" :sttText="sttText" :sttCursorPosition="sttCursorPosition"
            :isStreaming="streaming" @send="sendMessage" @open-config="openAIConfig"
            @open-statistic="statisticDialogVisible = true" />

    </div>
    <!-- AI配置抽屉 -->
    <AIConfigDrawer v-if="sessionAiConfig !== null" v-model="drawerVisible" :config="sessionAiConfig" :chatId="chatId"
        :systemPrompt="chatMessages[0]" @update-config="updateSessionAiConfig" />

    <el-dialog v-model="statisticDialogVisible" fullscreen>
        <StatisticDialog :messages="chatMessages" />
        <template #footer>
            <div class="dialog-footer">
                <el-button @click="statisticDialogVisible = false">Cancel</el-button>
                <el-button type="primary" @click="statisticDialogVisible = false">
                    Confirm
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatMessages from '@/components/Chat/ChatMessages.vue'
import MessageStream from '@/components/Chat/MessageStream.vue'
import SuggestionsList from '@/components/Chat/SuggestionsList.vue'
import ChatInput from '@/components/Chat/ChatInput.vue'
import AIConfigDrawer from '@/components/Chat/AIConfigDrawer.vue'
import StatisticDialog from '@/components/Chat/StatisticDialog.vue'
import ThreeDotsLoader from '@/components/Svgs/ThreeDotsLoader.vue'
import { ChatWebSocketService, useChatWebSocket } from '@/common/chat-websocket-client'
import { processMarkdown } from '@/common/markdown-processor'
import { formatTimeNow, highlightPlayingSentence, scrollToBottom, delayScrollToBottom } from '@/common/utils'
import { Message, AIConfig, ProcessResult } from '@/common/type-interface'


// 路由与状态
const route = useRoute()
const router = useRouter()
const chatId = ref(-1)
const drawerVisible = ref(false)

// 聊天数据状态
const sessionAiConfig = ref<AIConfig | null>(null)
const chatMessages = ref<Message[]>([])
const sessionSuggestions = ref<string[]>([])
const sessionTitle = ref('')
const streaming = ref(false)
const isScrolledWhenStreaming = ref(false)
const isChatError = ref(false)
const streamResponse = ref('')
const isSentNoStream = ref(false)
const statisticDialogVisible = ref(false)

// 输入状态
const isSpeechRecognizing = ref(false)
const sttText = ref('')
const sttCursorPosition = ref(0)

// WebSocket连接
const webSocket = ref<ChatWebSocketService | null>(null)

// 初始化
onMounted(() => {
    watchRouteChange()
})

onBeforeUnmount(() => {
    document.title = 'Voichai'
})

router.beforeEach(async (to, from, next) => {
    // 关闭 WebSocket
    if (!isSentNoStream.value && !streaming.value) {
        webSocket.value?.close()
    } else {
        webSocket.value?.sendStopResponse()
        await new Promise(resolve => setTimeout(resolve, 250))
        webSocket.value?.close()
    }
    next()
})

// 监听路由变化
const watchRouteChange = () => {
    watch(() => route.params.id, (newId) => {
        const newChatId = newId ? Number(newId) : -1
        if (newChatId !== chatId.value) {
            chatId.value = newChatId
            setupWebSocket()
        }
    }, { immediate: true })
}

// 初始化WebSocket
const setupWebSocket = () => {
    webSocket.value = useChatWebSocket(chatId.value)
    if (webSocket.value) {
        webSocket.value.handleMessage = (message: any) => {
            handleWebSocketMessage(message)
        }
    }
}

// 处理WebSocket消息
const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
        case 'session_title':
            sessionTitle.value = message.data.title
            document.title = sessionTitle.value || 'Voichai'
            break
        case 'session_messages':
            handleSessionMessages(message.data.messages)
            break
        case 'parse_request':
            handleParseRequest(message.data)
            break
        case 'stream_response':
            handleStreamResponse(message.data)
            break
        case 'session_suggestions':
            sessionSuggestions.value = message.data.suggestions
            delayScrollToBottom('smooth')
            break
        case 'session_ai_config':
            sessionAiConfig.value = message.data.ai_config
            sessionSuggestions.value = message.data.ai_config.suggestions
            break
        case 'the_sentence_playing':
            updatePlayingSentence(message.data)
            break
        case 'update_message':
            updateMessageContent(message.data)
            break
        case 'delete_message':
            removeMessage(message.data)
            break
        case 'speech_recognizing':
            handleSpeechRecognizing(message.data)
            break
        case 'stop_speech_recognize':
            isSpeechRecognizing.value = false
            break
        case 'error_session_not_exist':
            router.push('/')
            break
    }
}

// 处理会话消息
const handleSessionMessages = (messages: any[]) => {
    const receivedTime = new Date().getTime()
    chatMessages.value = messages.map(msg => {
        const parsedText = msg.parsed_text || ''
        let result = JSON.parse(parsedText)
        // if (!result || !result.html || !result.sentences) {
        //     result = processMarkdown(msg.raw_text, msg.id)
        // }
        return {
            message_id: msg.id,
            raw_text: msg.raw_text,
            processed_html: result.html,
            sentences: result.sentences,
            time: msg.timestamp,
            role: msg.role,
            is_playing: false
        }
    })
    console.log("Parsed messages time in milliseconds:", new Date().getTime() - receivedTime)
    delayScrollToBottom('instant')
}

// 处理解析请求
const handleParseRequest = (data: any) => {
    if (data.type === 'user_message') {
        addUserMessage(data.data)
    } else if (data.type === 'ai_response') {
        addAssistantMessage(data.data)
    }
    if (!isScrolledWhenStreaming.value) {
        scrollToBottom('smooth')
    }
}

// 添加用户消息
const addUserMessage = (data: any) => {
    const result = processMarkdown(data.user_message, data.message_id)
    chatMessages.value.push({
        message_id: data.message_id,
        raw_text: data.user_message,
        processed_html: result.html,
        sentences: result.sentences,
        time: formatTimeNow(),
        role: 'user',
        is_playing: false
    })
    webSocket?.value?.sendParsedUserMessage(data.message_id, result.html, result.sentences)
}


const handleChatMessagesForResponse = (data: any, result: ProcessResult) => {
    const lastIndex = chatMessages.value.length - 1
    if (chatMessages.value.length > 0 && chatMessages.value[lastIndex].message_id === data.message_id) {
        // 如果最后一条消息是流式响应的占位符，更新它
        chatMessages.value[lastIndex].processed_html = result.html
        chatMessages.value[lastIndex].raw_text = data.response
        chatMessages.value[lastIndex].sentences = result.sentences
    } else {
        // 否则添加新消息
        chatMessages.value.push({
            message_id: data.message_id,
            raw_text: data.response,
            processed_html: result.html,
            sentences: result.sentences,
            time: formatTimeNow(),
            role: 'assistant',
            is_playing: false
        })
    }
}

// 添加助手消息
const addAssistantMessage = (data: any) => {
    const result = processMarkdown(data.response, data.message_id)
    handleChatMessagesForResponse(data, result)
    data.sentences = result.sentences
    webSocket?.value?.sendParsedAiResponse(data.message_id, result.html, result.sentences, data.response)

    // 自动播放
    if (sessionAiConfig.value?.auto_play) {
        webSocket?.value?.sendGenerateAudioFiles(data.message_id, 0, 0)
        setTimeout(() => {
            webSocket?.value?.sendPlayMessage(data.message_id);
        }, 1000)
    }

}

const handleChatMessagesForStreaming = (data: any) => {
    const message_id = data.message_id
    const lastIndex = chatMessages.value.length - 1
    const result = processMarkdown(data.response, message_id)
    if (lastIndex >= 0 && chatMessages.value[lastIndex].message_id === message_id) {
        chatMessages.value[lastIndex].processed_html = result.html
        chatMessages.value[lastIndex].raw_text = data.response
    }
    else {
        isScrolledWhenStreaming.value = false
        chatMessages.value.push({
            message_id: message_id,
            raw_text: data.response,
            processed_html: result.html,
            sentences: [],
            time: formatTimeNow(),
            role: 'assistant',
            is_playing: false
        })
    }
}

// 处理流式响应
const handleStreamResponse = (data: any) => {
    streaming.value = data.is_streaming
    isSentNoStream.value = false
    isChatError.value = data.is_chat_error
    streamResponse.value = data.response
    if (!data.is_chat_error) {
        handleChatMessagesForStreaming(data)
    }
    if (!isScrolledWhenStreaming.value) {
        scrollToBottom('smooth')
    }
}

// 更新正在播放的句子
const updatePlayingSentence = (data: any) => {
    const message_id = data.message_id
    const sentence_id = data.sentence_id
    const message = chatMessages.value.find(msg => msg.message_id === message_id)
    if (message) {
        message.is_playing = sentence_id !== -1
    }
    console.log("the_sentence_playing:", message_id, sentence_id)
    highlightPlayingSentence(data.message_id, data.sentence_id)
}

// 更新消息内容
const updateMessageContent = (data: any) => {
    const message_id = data.message_id
    const raw_text = data.raw_text
    const message = chatMessages.value.find(msg => msg.message_id === message_id)
    console.log("update_message:", message_id, raw_text)
    if (message) {
        const result = processMarkdown(raw_text, message_id)
        message.raw_text = raw_text
        message.sentences = result.sentences
        message.processed_html = result.html
    }
}

// 删除消息
const removeMessage = (data: any) => {
    const message_id = data.message_id
    const index = chatMessages.value.findIndex(msg => msg.message_id === message_id)
    if (index !== -1) {
        chatMessages.value.splice(index, 1)
    }
}

// 发送消息
const sendMessage = (text: string) => {
    if (!text.trim() || !chatId.value) return
    webSocket?.value?.sendUserInput(text)
    isSentNoStream.value = true
    if (isSpeechRecognizing.value) {
        webSocket?.value?.sendStopSpeechRecognition()
    }
    sessionSuggestions.value = []
    // sessionSuggestions.value = ["", "", ""]
    scrollToBottom('smooth')
}

// 处理语音识别中消息
const handleSpeechRecognizing = (data: any) => {
    isSpeechRecognizing.value = true
    sttText.value = data.stt_text
    sttCursorPosition.value = data.cursor_position
}

// AI配置相关
const openAIConfig = () => {
    drawerVisible.value = true
}

const updateSystemPrompt = (message_id: number, raw_text: string) => {
    const result = processMarkdown(raw_text, message_id)
    webSocket?.value?.sendUpdateMessage(message_id, raw_text, result.html, result.sentences)
}

const updateSessionAiConfig = (config: AIConfig, systemPromptMessageId: number, newRawText: string, oldRawText: string) => {
    if (newRawText !== oldRawText) {
        updateSystemPrompt(systemPromptMessageId, newRawText)
    }
    webSocket?.value?.sendUpdateSessionConfig(config)
    drawerVisible.value = false
}

</script>
