<template>
    <div class="sidebar" @click="handleSidebarClick" @scroll="handleScroll">
        <el-menu ref="menuRef" :default-active="activeMenu" :collapse="isCollapse" :default-openeds="['chats']"
            @open="handleOpen" @close="handleClose" class="sidebar-menu">

            <el-menu-item index="collapse" @click="toggleCollapse" style="padding-left: 2px;">
                <el-icon v-show="!isCollapse">
                    <Fold />
                </el-icon>
                <el-icon v-show="isCollapse">
                    <Expand />
                </el-icon>
                <span style="font-weight: bold;">Voichai</span>
            </el-menu-item>


            <el-menu-item index="new_chat" @click="createNewSession" style="padding-left: 2px;">
                <el-icon>
                    <Plus />
                </el-icon>
                <span>新对话</span>
            </el-menu-item>

            <el-menu-item key="/" index="home" @click="navigateTo('/')" style="padding-left: 8px;">
                <el-icon>
                    <VscHome />
                </el-icon>
                <span>首页</span>
            </el-menu-item>

            <el-sub-menu index="chats">
                <template #title>
                    <el-icon>
                        <Clock />
                    </el-icon>
                    <span>历史对话</span>
                </template>
                <Session-list :sessions="chatSessions" :webSocket="webSocket" @navigate="navigateTo" />
            </el-sub-menu>
        </el-menu>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, Expand, Fold, Clock } from '@element-plus/icons-vue'
import { VscHome } from 'vue-icons-plus/vsc'
import SessionList from '@/components/Sidebar/SessionList.vue'
import { useWebSocket } from '@/common/websocket-client'
import { processMarkdown } from '@/common/markdown-processor'
import { ElMenu } from 'element-plus'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const menuRef = ref<InstanceType<typeof ElMenu>>();
const chatSessions = ref<any[]>([])
const sidebarWidth = ref('0px')
const siderbarScrollTimeoutId = ref<NodeJS.Timeout | null>(null)


// 连接WebSocket
const webSocket = useWebSocket('ws://localhost:4999/ws/aichat/spa')
webSocket.handleMessage = (message: any) => {
    handleWebSocketMessage(message)
}

// 处理WebSocket消息
const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
        case 'parse_markdown':
            parseMarkdown(message)
            break
        case 'parse_create_session':
            parseMarkdown(message)
            break
        case 'all_sessions':
            loadSessions(message.data.sessions)
            break
        case 'update_session_ai_avatar':
            updateSessionAiAvatar(message.data.session_id, message.data.ai_avatar_url)
            break
        case 'update_session_title':
            updateSessionTitle(message.data.session_id, message.data.title)
            break
        case 'update_session_top':
            updateSessionTop(message.data.session_id, message.data.top)
            break
        case 'delete_session':
            deleteSession(message.data.session_id)
            break
        case 'new_session':
            addNewSession(message.data)
            break
    }
}

const handleScroll = () => {
    // 当滚动时，设置body的滚动条背景颜色
    if (siderbarScrollTimeoutId.value) {
        clearTimeout(siderbarScrollTimeoutId.value)
    }
    const scrollbarBackground = getComputedStyle(document.documentElement)
        .getPropertyValue('--scrollbar-background');
    document.documentElement.style.setProperty('--sidebar-scrollbar-background', scrollbarBackground)
    siderbarScrollTimeoutId.value = setTimeout(() => {
        document.documentElement.style.setProperty('--sidebar-scrollbar-background', 'rgba(0, 0, 0, 0)')
        siderbarScrollTimeoutId.value = null
    }, 1000)
}

const parseMarkdown = (message: any) => {
    const messageId = message.data.message_id
    const raw_text = message.data.raw_text
    const result = processMarkdown(raw_text, messageId)
    webSocket.send({
        type: message.type,
        data: {
            html: result.html,
            sentences: result.sentences,
            ...message.data
        }
    })
}

// 加载会话数据
const loadSessions = (sessionsData: any[]) => {
    chatSessions.value = sessionsData.map(session => ({
        path: `/chat/${session.id}`,
        title: session.title,
        config: JSON.parse(session.ai_config),
        id: session.id
    }))
    sortAndUpdateHistory()
}

const sortSessions = (sessions: any[]) => {
    return sessions.sort((a, b) => {
        const aTop = a.config?.top ?? false
        const bTop = b.config?.top ?? false

        // 置顶会话优先
        if (aTop && !bTop) return -1
        if (!aTop && bTop) return 1

        // 按最后活跃时间排序
        const aTime = a.config?.last_active_time ?? 0
        const bTime = b.config?.last_active_time ?? 0

        return bTime - aTime // 降序排列，最新的在前
    })
}

// 排序并更新历史会话
const sortAndUpdateHistory = () => {
    chatSessions.value = sortSessions(chatSessions.value)
    handleSidebarClick()
}

// 更新会话AI头像
const updateSessionAiAvatar = (sessionId: number, aiAvatarUrl: string) => {
    const session = chatSessions.value.find(item => item.id === sessionId)
    if (session) {
        session.config.ai_avatar_url = aiAvatarUrl
    }
}

// 更新会话标题
const updateSessionTitle = (sessionId: number, title: string) => {
    const session = chatSessions.value.find(item => item.id === sessionId)
    if (session) {
        session.title = title
    }
}

// 更新会话置顶状态
const updateSessionTop = (sessionId: number, top: boolean) => {
    const session = chatSessions.value.find(item => item.id === sessionId)
    if (session) {
        session.config.top = top
        sortAndUpdateHistory()
    }
}

// 删除会话
const deleteSession = (sessionId: number) => {
    const index = chatSessions.value.findIndex(item => item.id === sessionId)
    if (index !== -1) {
        chatSessions.value.splice(index, 1)
    }
}

// 添加新会话
const addNewSession = (sessionData: any) => {
    chatSessions.value.push({
        path: `/chat/${sessionData.session_id}`,
        title: sessionData.title,
        config: sessionData.config,
        id: sessionData.session_id
    })
    sortAndUpdateHistory()
    setTimeout(() => {
        router.push(`/chat/${sessionData.session_id}`)
    }, 300)
}

// 创建新会话
const createNewSession = () => {
    webSocket.send({
        type: 'create_session',
        data: {}
    })
}

// 侧边栏点击处理
const handleSidebarClick = () => {
    const sidebar = document.querySelector('.sidebar')
    if (sidebar) {
        setTimeout(() => {
            const newSidebarWidth = sidebar.clientWidth + 20 + 'px'
            if (sidebarWidth.value !== newSidebarWidth) {
                sidebarWidth.value = newSidebarWidth
                document.documentElement.style.setProperty('--main-content-left-margin', sidebarWidth.value)
            }
            highlightActiveItem()
        }, 500)
    }
}

// 切换折叠状态
const toggleCollapse = () => {
    isCollapse.value = !isCollapse.value
    // 使用 Exposes 中的 openMenu 方法主动打开子菜单
    if (!isCollapse.value && menuRef.value) {
        (menuRef.value as any).open('chats');
    }
}

// 导航到指定路径
const navigateTo = (path: string) => {
    router.push(path)
}

// 高亮当前活动项
const highlightActiveItem = () => {
    const item = document.getElementById(`chat-item-${route.path}`)
    if (item) {
        item.style.color = 'rgb(24, 144, 255)'
        item.style.fontWeight = 'bold'
        item.style.backgroundColor = "var(--sidebar-menu-active-bg-color)"
    }
}

const switchHighlightActiveItem = (newPath: string, oldPath: string) => {
    const newItem = document.getElementById(`chat-item-${newPath}`)
    const oldItem = document.getElementById(`chat-item-${oldPath}`)

    if (oldItem) {
        oldItem.style.color = ''
        oldItem.style.fontWeight = ''
        oldItem.style.backgroundColor = ''
    }

    if (newItem) {
        newItem.style.color = 'rgb(24, 144, 255)'
        newItem.style.fontWeight = 'bold'
        newItem.style.backgroundColor = "var(--sidebar-menu-active-bg-color)"
    }
}

// 当前活动菜单项
const activeMenu = computed(() => {
    return route.path
})

// 监听路由变化
watch(activeMenu, switchHighlightActiveItem)

// 菜单事件处理
const handleOpen = (key: string, keyPath: string[]) => {
    console.log('菜单打开:', key, keyPath)
}

const handleClose = (key: string, keyPath: string[]) => {
    console.log('菜单关闭:', key, keyPath)
}
</script>