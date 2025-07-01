<template>
    <div class="app-container">

        <div class="sidebar" @click="siderbar_click">
            <el-menu :default-active="activeMenu" class="el-menu-vertical-demo" :collapse="isCollapse"
                @open="handleOpen" @close="handleClose">
                <el-menu-item index="collapse" @click="isCollapse = !isCollapse" style="padding-left: 2px;">
                    <el-icon v-show="!isCollapse">
                        <Fold />
                    </el-icon>
                    <el-icon v-show="isCollapse">
                        <Expand />
                    </el-icon>
                    <span>AI Chat</span>
                </el-menu-item>

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

                <el-sub-menu index="history" @click="highlight_actived_item_by_background_font_size(route.path, '')"
                    style="padding-left: 2px;">
                    <template #title>
                        <el-icon>
                            <Clock />
                        </el-icon>
                        <span>历史对话</span>
                    </template>
                    <el-menu-item v-for="item in historyItems" :key="item.path" :index="item.path"
                        :id="`chat-item-${item.path}`" class="custom-menu-item" @click="navigateTo(item.path)"
                        style="padding-left: 2px;">
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

                                    <el-button :type="''" :icon="EditPen" text style="padding-right: 50%;"
                                        @click="rename_dialog_visible = true">
                                        重命名
                                    </el-button>

                                    <el-popconfirm placement="right" confirm-button-text="删除"
                                        confirm-button-type="danger" cancel-button-text="取消" :icon="Delete"
                                        icon-color="#FF4949" title="确定删除对话？"
                                        @confirm="delete_session(get_session_id(item.path))" @cancel="">
                                        <template #reference>
                                            <el-button :type="'danger'" :icon="Delete" text style="padding-right: 60%;">
                                                删除
                                            </el-button>
                                        </template>
                                    </el-popconfirm>
                                </div>
                                <template #reference>
                                    <el-icon class="hover-icon"
                                        @click.stop="rename_session.title = item.title; rename_session.session_id = get_session_id(item.path)">
                                        <MoreFilled />
                                    </el-icon>
                                </template>
                            </el-popover>
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

        <div class="main-content">
            <router-view />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, Plus, Expand, Fold, Menu, ChatDotSquare, Clock, MoreFilled, Delete, EditPen } from '@element-plus/icons-vue'
import { useWebSocket, WebSocketService } from '@/common/websocket-client'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor'
import debounce from 'lodash/debounce'

const route = useRoute()
const router = useRouter()
const chat_popover_show = ref(false)
const rename_dialog_visible = ref(false)
const rename_session_name = ref('')
const rename_session = ref({ session_id: -1, title: '' })
let historyItems = ref<any[]>([])
const sentences = ref<SentenceInfo[]>([])
let currentWebSocket: WebSocketService
const sidebar_width = ref('0px');

const siderbar_click = () => {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        setTimeout(() => {
            const new_sidebar_width = sidebar.clientWidth + 20 + 'px';
            if (sidebar_width.value !== new_sidebar_width) {
                sidebar_width.value = new_sidebar_width;
                document.documentElement.style.setProperty('--main-content-left-margin', sidebar_width.value);
            }
        }, 100);

    }
}

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

const delete_session = (session_id: number) => {
    const message = {
        type: 'delete_session',
        data: {
            session_id: session_id,
        },
    }
    console.log(message)
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
                    siderbar_click()
                    setTimeout(() => {
                        highlight_actived_item_by_background_font_size(route.path, "")
                    }, 300)
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
                case 'delete_session':
                    {
                        const session_id = message.data.session_id
                        for (let i = 0; i < historyItems.value.length; i++) {
                            if (historyItems.value[i].path == `/history/${session_id}`) {
                                historyItems.value.splice(i, 1)
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

// 高亮当前活动项
const highlight_actived_item_by_background_font_size = (newValue: string, oldValue: string) => {
    const newItem = document.getElementById(`chat-item-${newValue}`)
    const oldItem = document.getElementById(`chat-item-${oldValue}`)
    if (oldItem) {
        oldItem.style.backgroundColor = ''
        oldItem.style.fontSize = ''
        oldItem.style.fontWeight = ''
        oldItem.style.color = ''
    }
    if (newItem) {
        // newItem.style.backgroundColor = 'rgb(238,245,254)'
        // newItem.style.fontSize = '1.1rem'
        newItem.style.color = 'rgb(24,144,255)'
        newItem.style.fontWeight = 'bold'
    }
}

// 监听路由变化
watch(activeMenu, highlight_actived_item_by_background_font_size)

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
:root {
    --main-content-left-margin: 300px;
}

.app-container {
    display: flex;
    height: 100vh;
}

.sidebar {
    position: fixed;
    max-width: 300px;
    border-right: 1px solid #909399;
    box-sizing: border-box;
    overflow-y: auto;
    height: 100vh;
    --el-menu-active-color: #409EFF;
}

.main-content {
    flex: 1;
    padding: 20px;
    margin-left: var(--main-content-left-margin);
    transition: margin-left 0.3s;
}

.custom-menu-item {
    position: relative;
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
    margin-right: 10px;
    /* 与右侧图标保持间距 */
}

.hover-icon {
    opacity: 0;
    /* 默认隐藏 */
    transition: opacity 0.2s;
    /* 添加淡入淡出动画 */
    position: absolute;
    /* 绝对定位到右侧 */
    right: 2px;
    /* 调整右侧距离 */
}

.custom-menu-item:hover .hover-icon {
    opacity: 1;
    /* 鼠标悬停时显示 */
}
</style>