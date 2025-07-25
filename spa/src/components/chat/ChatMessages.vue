<template>
    <div class="chat-messages-container">
        <el-skeleton v-if="loading" :rows="5" animated />
        <div v-if="!loading" class="chat-message" v-for="message in visibleMessages" :key="message.message_id">
            <MessageBubble :websocket="websocket" :message="message"
                :showRefreshButton="message.message_id === maxAssistantMessageId" @regenerate="handleRegenerate"
                @update-message="handleUpdateMessage" />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, watchEffect, onMounted, watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import MessageBubble from '@/components/Chat/MessageBubble.vue'
import { processMarkdown } from '@/common/markdown-processor'
import { ChatWebSocketService } from '@/common/chat-websocket-client'
import { Message } from '@/common/type-interface'

// 消息ID跟踪
const maxUserMessageId = ref(-1)
const maxAssistantMessageId = ref(-1)

const route = useRoute()
const visibleMessages = ref<any[]>([])
const loading = ref(false)
const hasMoreMessages = ref(true)
const pageSize = ref(20) // 每页显示的消息数量
const currentPage = ref(1)
const bodyScrollTimeoutId = ref<NodeJS.Timeout | null>(null)
const scrollTimeoutId = ref<NodeJS.Timeout | null>(null)
const lastScrollTop = ref(0)
const scrolledCount = ref(0)

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
    }
})

// 定义组件输出事件
const emits = defineEmits<{
    (e: 'send-message', text: string): void
    (e: 'scroll-up'): void
}>()

const initVisibleMessages = async () => {
    visibleMessages.value = []
    currentPage.value = 1
    loading.value = false
    hasMoreMessages.value = true
    await loadMoreMessages()
}

watch(() => route.params.id, async () => {
    if (visibleMessages.value.length > 0) {
        await initVisibleMessages()
    }
}, { immediate: true })

// 计算当前可见的消息
const updateVisibleMessages = () => {
    const startIndex = - ((currentPage.value - 1) * pageSize.value)
    const endIndex = props.messages.length

    visibleMessages.value = props.messages.slice(startIndex, endIndex)
    hasMoreMessages.value = startIndex >= - props.messages.length
}

// 加载更多消息
const loadMoreMessages = async () => {
    if (loading.value || !hasMoreMessages.value) return
    loading.value = true
    currentPage.value++
    // await new Promise(resolve => setTimeout(resolve, 3000))
    updateVisibleMessages()
    loading.value = false
}

onMounted(async () => {
    // 添加滚动事件监听器
    await loadMoreMessages()
    window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
    // 移除滚动事件监听器，防止内存泄漏
    window.removeEventListener('scroll', handleScroll)
})

const autoHideScrollbar = () => {
    if (bodyScrollTimeoutId.value) {
        clearTimeout(bodyScrollTimeoutId.value)
    }
    const scrollbarBackground = getComputedStyle(document.documentElement)
        .getPropertyValue('--scrollbar-background');
    document.documentElement.style.setProperty('--body-scrollbar-background', scrollbarBackground)
    bodyScrollTimeoutId.value = setTimeout(() => {
        document.documentElement.style.setProperty('--body-scrollbar-background', 'rgba(0, 0, 0, 0)')
        bodyScrollTimeoutId.value = null
    }, 1000)
}

const handleUpScroll = () => {
    if (window.scrollY > lastScrollTop.value) {
        // 向下滚动
        scrolledCount.value = 0
    } else {
        // 向上滚动
        scrolledCount.value += 1
        scrollTimeoutId.value && clearTimeout(scrollTimeoutId.value)
        scrollTimeoutId.value = setTimeout(() => {
            scrolledCount.value = 0
            scrollTimeoutId.value = null
        }, 1000)
        if (scrolledCount.value >= 10) {
            emits('scroll-up')
            scrolledCount.value = 0
        }
    }
    lastScrollTop.value = window.scrollY
}

// 滚动事件处理
const handleScroll = () => {
    handleUpScroll()
    autoHideScrollbar()
    if (window.scrollY <= 500 && hasMoreMessages.value) {
        // 当滚动到顶部一定距离时加载更多
        loadMoreMessages()
    }
}


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
        console.log('maxUserMessageId.value:', maxUserMessageId.value)
        console.log('maxAssistantMessageId.value:', maxAssistantMessageId.value)
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
    updateVisibleMessages()
    maxUserMessageId.value = getMaxMessageId('user')
    maxAssistantMessageId.value = getMaxMessageId('assistant')
})

</script>
