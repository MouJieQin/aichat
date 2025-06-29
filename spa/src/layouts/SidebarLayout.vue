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
                <el-menu-item index="new_chat" @click="create_new_session" style="padding-left: 2px;">
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
                        @click="navigateTo(item.path)" style="padding-left: 8px;">
                        {{ item.title }}
                    </el-menu-item>
                </el-sub-menu>
                <!-- 历史对话菜单 -->
                <el-sub-menu index="history" style="padding-left: 2px;">
                    <template #title>
                        <el-icon>
                            <Clock />
                        </el-icon>
                        <span>历史对话</span>
                    </template>
                    <el-menu-item v-for="item in historyItems" :key="item.path" :index="item.path"
                        class="custom-menu-item" @click="navigateTo(item.path)" style="padding-left: 2px;">
                        <template #title>
                            <el-icon>
                                <ChatDotSquare />
                            </el-icon>
                            <span class="truncate-text" :title="item.title">{{ item.title }}</span>

                            <el-popover placement="top-end" :width="200" trigger="click">
                                <div>
                                    <el-button :type="''" :icon="ChatDotSquare" text
                                        style="padding-right: 50%;margin-left: 7%;"
                                        @click.stop="chat_popover_show = false">
                                        置顶
                                    </el-button>
                                    <el-button :type="''" :icon="ChatDotSquare" text style="padding-right: 60%;"
                                        @click="rename_dialog_visible = true">
                                        编辑
                                    </el-button>
                                    <el-button :type="'danger'" :icon="ChatDotSquare" text style="padding-right: 60%;">
                                        删除
                                    </el-button>
                                </div>
                                <template #reference>
                                    <el-icon class="hover-icon"
                                        @click.stop="rename_session.title = item.title; rename_session.session_id = get_session_id(item.path)">
                                        <MoreFilled />
                                    </el-icon>
                                </template>
                            </el-popover>

                            <!-- <el-icon class="hover-icon" @click.stop="showItemMenu(item)">
                                <MoreFilled />
                            </el-icon> -->


                        </template>
                    </el-menu-item>
                </el-sub-menu>
            </el-menu>
        </div>

        <el-dialog v-model="rename_dialog_visible" title="编辑对话名称" width="500">
            <el-form-item>
                <el-input v-model="rename_session.title" autocomplete="off" />
            </el-form-item>
            <template #footer>
                <div class="dialog-footer">
                    <el-button @click="rename_dialog_visible = false">Cancel</el-button>
                    <el-button type="primary" @click="update_session_title">
                        Confirm
                    </el-button>
                </div>
            </template>
        </el-dialog>

        <!-- 主内容区域 -->
        <div class="main-content">
            <router-view />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, Plus, Menu, ChatDotSquare, Clock, MoreFilled } from '@element-plus/icons-vue'
import { useWebSocket, WebSocketService } from '@/common/websocket-client'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor'

const route = useRoute()
const router = useRouter()
const chat_popover_show = ref(false)
const rename_dialog_visible = ref(false)
const rename_session_name = ref('')
const rename_session = ref({ session_id: -1, title: '' })
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

const get_session_id = (path: string) => {
    return Number(path.split('/')[2])
}

const update_session_title = () => {
    const message = {
        type: 'update_session_title',
        data: {
            session_id: rename_session.value.session_id,
            title: rename_session.value.title,
        },
    }
    console.log(message)
    currentWebSocket.send(message)
    rename_dialog_visible.value = false
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
                case 'update_session_title':
                    {
                        const session_id = message.data.session_id
                        const title = message.data.title
                        for (const item of historyItems.value) {
                            if (item.path == `/history/${session_id}`) {
                                item.title = title
                                break
                            }
                        }
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
    width: 300px;
    border-right: 1px solid #e6e6e6;
    padding: 10px;
    box-sizing: border-box;
    overflow-y: auto;
    max-height: 100vh;
}

.main-content {
    flex: 1;
    overflow-y: hidden;
    padding: 20px;
}

.custom-menu-item {
    position: relative;
    /* 为绝对定位提供参考 */
}

.custom-menu-item .el-menu-item__title {
    display: flex;
    align-items: center;
}

.truncate-text {
    flex: 1;
    /* 文本区域占据剩余空间 */
    max-width: calc(100% - 40px);
    white-space: nowrap;
    overflow: hidden;
    text-align: left;
    text-overflow: ellipsis;
    margin-right: 8px;
    /* 与右侧图标保持间距 */
}

.hover-icon {
    opacity: 0;
    /* 默认隐藏 */
    transition: opacity 0.2s;
    /* 添加淡入淡出动画 */
    position: absolute;
    /* 绝对定位到右侧 */
    right: 10px;
    /* 调整右侧距离 */
}

.custom-menu-item:hover .hover-icon {
    opacity: 1;
    /* 鼠标悬停时显示 */
}
</style>