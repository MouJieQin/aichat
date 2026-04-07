<!-- src/views/ChatLayout.vue -->
<template>
    <!-- 自定义 macOS 标题栏（仅 macOS 显示，包含 Pin 置顶按钮） -->
    <div class="mac-titlebar">
        <button @click="handlePinClick" class="pin-button" :title="isPinned ? '取消置顶' : '窗口置顶'">
            {{ isPinned ? '📍' : '📌' }}
        </button>
        <span class="floating-window-title">{{ title }}</span>
    </div>
</template>

<script lang="ts" setup>
import { ChatWebSocketService } from '@/common/chat-websocket-client'
import { useRoute } from 'vue-router'

const route = useRoute()
const props = defineProps({
    webSocket: {
        type: ChatWebSocketService,
        required: true
    },
    title: {
        type: String,
        required: true,
        default: 'Voichai'
    },
    isPinned: {
        type: Boolean,
        required: true,
        default: false
    }
})

const handlePinClick = () => {
    props.webSocket.sendToggleFloatingWindowPin(route.fullPath)
}

</script>
