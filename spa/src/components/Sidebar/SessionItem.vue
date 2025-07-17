<!-- src/components/Sidebar/SessionItem.vue -->
<template>
    <el-menu-item :index="session.path" :id="'chat-item-' + session.path" class="custom-menu-item"
        @click="handleNavigate">
        <template #title>
            <el-icon>
                <ChatDotSquare />
            </el-icon>

            <span class="truncate-text" :title="session.title">{{ session.title }}</span>

            <el-icon v-if="session.config.top" style="font-size: 12px; margin-right: 0px;">
                <LuPin style="opacity: 0.5;" />
            </el-icon>

            <session-context-menu :session="session" :webSocket="webSocket" />
        </template>
    </el-menu-item>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import SessionContextMenu from '@/components/Sidebar/SessionContextMenu.vue'
import { ChatDotSquare, More } from '@element-plus/icons-vue'
import { LuPin } from 'vue-icons-plus/lu'
import { WebSocketService } from '@/common/websocket-client'

const props = defineProps({
    session: {
        type: Object,
        required: true,
        default: () => ({
            path: '',
            title: '',
            config: {
                top: false
            },
            session_id: 0
        })
    },
    webSocket: {
        type: WebSocketService,
        required: true
    }
})

const emits = defineEmits([
    'navigate',
])

// 处理导航
const handleNavigate = () => {
    emits('navigate', props.session.path)
}

</script>
