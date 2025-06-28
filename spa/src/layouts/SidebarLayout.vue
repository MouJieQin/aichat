<template>
    <div class="app-container">
        <!-- 侧边栏区域 -->
        <div class="sidebar">
            <el-radio-group v-model="isCollapse" style="margin-bottom: 20px">
                <el-radio-button :value="false">expand</el-radio-button>
                <el-radio-button :value="true">collapse</el-radio-button>
            </el-radio-group>
            <el-menu :default-active="activeMenu" class="el-menu-vertical-demo" :collapse="isCollapse"
                @open="handleOpen" @close="handleClose">
                <!-- 其他一级菜单 -->
                <el-menu-item index="new_chat" @click="create_new_session">
                    <el-icon>
                        <Plus />
                    </el-icon>
                    <span>新对话</span>
                </el-menu-item>
                <el-sub-menu index="navigator">
                    <template #title>
                        <el-icon>
                            <location />
                        </el-icon>
                        <span>导航</span>
                    </template>
                    <el-menu-item v-for="item in navigatorItems" :key="item.path" :index="item.path"
                        @click="navigateTo(item.path)">
                        {{ item.title }}
                    </el-menu-item>
                </el-sub-menu>

                <!-- 历史对话菜单 -->
                <el-sub-menu index="history">
                    <template #title>
                        <el-icon>
                            <Clock />
                        </el-icon>
                        <span>历史对话</span>
                    </template>
                    <el-menu-item v-for="item in historyItems" :key="item.path" :index="item.path"
                        @click="navigateTo(item.path)">
                        <template #title>
                            <el-icon>
                                <ChatDotSquare />
                            </el-icon>
                            <span>{{ item.title }}</span>
                        </template>
                    </el-menu-item>
                </el-sub-menu>
            </el-menu>
        </div>

        <!-- 主内容区域 -->
        <div class="main-content">
            <router-view />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, Plus, Menu, ChatDotSquare, Clock } from '@element-plus/icons-vue'
import { useWebSocket, WebSocketService } from '@/common/websocket-client'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor'

const route = useRoute()
const router = useRouter()
let historyItems = ref<any[]>([])
const sentences = ref<SentenceInfo[]>([])
let currentWebSocket: WebSocketService

onMounted(() => {
    websocket_connect()
})

onBeforeUnmount(() => {
    currentWebSocket.close()
})

const create_new_session = () => {
    const message = {
        type: 'create_session',
        data: {
        },
    }
    currentWebSocket.send(message)
}

const request_all_sessions = () => {
    const message = {
        type: 'get_all_sessions',
        data: {
        },
    }
    currentWebSocket.send(message)
}

// 加载历史对话数据
const websocket_connect = async () => {
    try {
        currentWebSocket = useWebSocket('ws://localhost:4999/ws/aichat/spa')
        currentWebSocket.handleMessage = (message: any) => {
            console.log('receive message:', message)
            switch (message.type) {
                case 'all_sessions':
                    console.log('收到聊天消息:', message.data)
                    historyItems.value = []
                    for (const session of message.data) {
                        historyItems.value.push({
                            path: `/history/${session[0]}`,
                            title: session[1],
                        })
                    }
                    break
                case 'parse_request':
                    switch (message.data.type) {
                        case 'create_session':
                            const message_id = message.data.data.message_id
                            const session_id = message.data.data.session_id
                            const title = message.data.data.title
                            const system_prompt = message.data.data.system_prompt
                            const result = processMarkdown(system_prompt, message_id)
                            const msg = {
                                type: 'parsed_response',
                                data: {
                                    type: "create_session",
                                    data: {
                                        message_id: message_id,
                                        session_id: session_id,
                                        title: title,
                                        sentences: result.sentences,
                                    }
                                },
                            }
                            currentWebSocket.send(msg)
                        default:
                            break
                    }
                    break
                case 'new_session':
                    const session_id = message.data.session_id
                    const title = message.data.title
                    const system_prompt = message.data.system_prompt
                    historyItems.value.push({
                        path: `/history/${session_id}`,
                        title: title,
                    })
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
    }
}

// 侧边栏折叠状态
const isCollapse = ref(false)

// 当前活动菜单项
const activeMenu = computed(() => {
    return route.path
})

// 菜单项数据
const navigatorItems = ref([
    { path: '/', title: '首页' },
    { path: '/page1', title: '内容页面1' },
])

// 导航方法
const navigateTo = (path: string) => {
    router.push(path)
}

// 菜单事件处理
const handleOpen = (key: string, keyPath: string[]) => {
    console.log('Menu opened:', key, keyPath)
}

const handleClose = (key: string, keyPath: string[]) => {
    console.log('Menu closed:', key, keyPath)
}
</script>

<style scoped>
.app-container {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

.sidebar {
    width: 200px;
    border-right: 1px solid #e6e6e6;
    padding: 10px;
    box-sizing: border-box;
    overflow-y: auto;
    max-height: 100vh;
}

.main-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}
</style>