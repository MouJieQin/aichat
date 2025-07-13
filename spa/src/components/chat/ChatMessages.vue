<template>
    <div class="chat-messages-container">
        <div class="chat-message" v-for="message in messages" :key="message.message_id">
            <MessageBubble :websocket="websocket" :message="message"
                :showRefreshButton="message.message_id === maxAssistantMessageId" @regenerate="handleRegenerate"
                @update-message="handleUpdateMessage" />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, defineProps, defineEmits, watchEffect } from 'vue'
import MessageBubble from '@/components/Chat/MessageBubble.vue'
import { processMarkdown } from '@/common/markdown-processor'
import { ChatWebSocketService } from '@/common/chat-websocket-client'
import { Message } from '@/common/type-interface'

// 消息ID跟踪
const maxUserMessageId = ref(-1)
const maxAssistantMessageId = ref(-1)

const props = defineProps({
    websocket: {
        type: ChatWebSocketService,
        required: true,
        default: null
    },
    messages: {
        type: Array as () => Message[],
        required: true,
        default: () => []
    },
})

// 定义组件输出事件
const emits = defineEmits<{
    (e: 'send-message', text: string): void
}>()

const handleRegenerate = () => {
    const message = props.messages.find(msg => msg.message_id === maxUserMessageId.value)
    if (message) {
        const lastUserInput = message.raw_text
        deleteMessage(maxAssistantMessageId.value)
        deleteMessage(maxUserMessageId.value)
        // make sure the message is deleted before sending the new message
        setTimeout(() => {
            emits('send-message', lastUserInput)
        }, 100)
    }
}

const handleUpdateMessage = (messageId: number, rawText: string) => {
    if (messageId !== maxUserMessageId.value) {
        const result = processMarkdown(rawText, messageId)
        props.websocket.sendUpdateMessage(messageId, rawText, result.html, result.sentences)
    } else {
        if (maxAssistantMessageId.value > maxUserMessageId.value) {
            deleteMessage(maxAssistantMessageId.value)
        }
        deleteMessage(maxUserMessageId.value)
        // make sure the message is deleted before sending the new message
        setTimeout(() => {
            emits('send-message', rawText)
        }, 100)
    }
}

const deleteMessage = (messageId: number) => {
    props.websocket.sendDeleteMessage(messageId)
}

// 计算最大消息ID
const getMaxMessageId = (role: string) => {
    const messages = props.messages.filter(m => m.role === role)
    return messages.length ? Math.max(...messages.map(m => m.message_id)) : -1
}

watchEffect(() => {
    maxUserMessageId.value = getMaxMessageId('user')
    maxAssistantMessageId.value = getMaxMessageId('assistant')
})

</script>
