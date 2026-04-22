<!-- src/views/ChatLayout.vue -->
<template>
    <!-- 自定义 macOS 标题栏（仅 macOS 显示，包含 Pin 置顶按钮） -->
    <div class="mac-titlebar">
        <div class="floating-window-title">
            <span>{{ title }}</span>
        </div>
        <div class="pin-button">
            <el-button :icon="props.isPinned ? BsPinAngleFill : BsPin" text @click="handlePinClick"
                :title="isPinned ? '取消置顶' : '窗口置顶'" size="small" />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ChatWebSocketService } from '@/common/chat-websocket-client'
import { useRoute } from 'vue-router'
import { BsPin, BsPinAngleFill } from 'vue-icons-plus/bs'

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
    props.webSocket.sendToggleFloatingWindowPin(!props.isPinned)
}

</script>
