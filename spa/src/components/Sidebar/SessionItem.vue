<!-- src/components/Sidebar/SessionItem.vue -->
<template>
    <el-menu-item :index="session.path" :id="'chat-item-' + session.path" class="custom-menu-item"
        @click="handleNavigate">
        <template #title>
            <el-icon>
                <ChatDotSquare />
            </el-icon>
            <span class="truncate-text" :title="session.title">{{ session.title }}</span>
            <el-icon v-if="session.config.top" style="padding-right: 10px;">
                <LuPin style="opacity: 0.5;" />
            </el-icon>

            <el-popover placement="top-end" :width="200" trigger="click" v-model:visible="showContextMenu"
                @visible-change="handleContextMenuVisible">
                <session-context-menu :session="session" :webSocket="webSocket"
                    @closePopover="handleContextMenuVisible" />
                <template #reference>
                    <el-icon class="hover-icon" @click.stop>
                        <More />
                    </el-icon>
                </template>
            </el-popover>
        </template>
    </el-menu-item>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { defineProps, defineEmits } from 'vue'
import SessionContextMenu from '@/components/Sidebar/SessionContextMenu.vue'
import { ChatDotSquare, More } from '@element-plus/icons-vue'
import { LuPin } from 'vue-icons-plus/lu'
import { WebSocketService } from '@/common/websocket-client'
import { on } from 'events'

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

const showContextMenu = ref(false)

// 处理导航
const handleNavigate = () => {
    emits('navigate', props.session.path)
    showContextMenu.value = false
}

// 处理上下文菜单显示/隐藏
const handleContextMenuVisible = (visible: boolean) => {
    if (!visible) {
        showContextMenu.value = false
    }
}
</script>
