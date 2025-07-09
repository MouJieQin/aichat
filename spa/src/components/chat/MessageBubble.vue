<template>
    <div class="message-bubble" @mouseenter="showControls = true" @mouseleave="showControls = false">
        <!-- 消息内容区域 -->
        <div class="message-content" :class="messageRoleClass">
            <!-- 正常显示模式 -->
            <div v-show="!isEditing" class="markdown-container" @click="handleSentenceClick">
                <p v-html="message.processed_html"></p>
            </div>

            <!-- 编辑模式 -->
            <div v-if="isEditing" class="edit-input-container">
                <el-input v-model="editContent" type="textarea" autosize placeholder="编辑消息内容..." />
            </div>

            <!-- 时间显示 -->
            <div class="message-time">{{ message.time }}</div>
        </div>

        <!-- 操作按钮组 -->
        <div class="controls-container" :class="controlRoleClass">
            <!-- 编辑状态按钮组 -->
            <el-button-group v-if="isEditing" class="edit-controls">
                <el-button :icon="Close" text @click="cancelEdit" tooltip="取消" />
                <el-button :icon="Check" text @click="confirmEdit" tooltip="确认" />
            </el-button-group>

            <!-- 常规操作按钮组 -->
            <el-button-group class="normal-controls" :style="{
                opacity: showControls && !isEditing ? '1' : '0',
                pointerEvents: showControls && !isEditing ? 'auto' : 'none'
            }">
                <!-- 播放/暂停按钮 -->
                <el-button :icon="(message.is_playing && !isPaused) ? VideoPause : VideoPlay" text
                    @click="handlePlayPause" tooltip="暂停" />

                <!-- 停止按钮 -->
                <el-button :icon="VscStopCircle" text @click="handlePlayStop" tooltip="停止" />

                <!-- 复制按钮 -->
                <el-button :icon="copySuccess ? Check : CopyDocument" text @click="handleCopy" tooltip="复制文本" />

                <!-- 重新生成按钮 -->
                <el-button v-if="showRefreshButton" :icon="Refresh" text @click="$emit('regenerate')" tooltip="重新生成" />

                <!-- 编辑按钮 -->
                <el-button :icon="Edit" text @click="enterEditMode" tooltip="编辑" />

                <!-- 更多操作下拉菜单 -->
                <el-dropdown trigger="click" placement="bottom-start">
                    <el-button :icon="More" text />
                    <template #dropdown>
                        <el-dropdown-menu>
                            <el-dropdown-item @click="handleDeleteAudio">
                                <el-icon>
                                    <Delete />
                                </el-icon>
                                <span>删除音频文件</span>
                            </el-dropdown-item>
                            <el-dropdown-item style="color: #ff4d4f" @click="handleDeleteConfirm">
                                <el-icon>
                                    <Delete />
                                </el-icon>
                                <span>删除消息</span>
                            </el-dropdown-item>
                        </el-dropdown-menu>
                    </template>
                </el-dropdown>
            </el-button-group>

        </div>

        <!-- 删除确认弹窗 -->
        <el-dialog v-model="showDeleteConfirm" title="确认删除" width="300px" align-center>
            <p>确定要删除这条消息吗？</p>
            <template #footer>
                <el-button @click="showDeleteConfirm = false">取消</el-button>
                <el-button type="danger" @click="confirmDelete">删除</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { defineProps, defineEmits } from 'vue'
import {
    Edit,
    CopyDocument,
    Delete,
    VideoPlay,
    VideoPause,
    Refresh,
    Close,
    Check,
    More
} from '@element-plus/icons-vue'
import { VscStopCircle } from 'vue-icons-plus/vsc'
import { Message } from '@/common/type-interface'
import { ChatWebSocketService } from '@/common/chat-websocket-client'

const props = defineProps({
    websocket: {
        type: ChatWebSocketService,
        required: true,
    },
    message: {
        type: Object as () => Message,
        required: true,
    },
    showRefreshButton: {
        type: Boolean,
        required: true,
        default: false
    }
})

// 定义组件输出事件
const emits = defineEmits<{
    (e: 'regenerate'): void
    (e: 'update-message', messageId: number, content: string): void
}>()

// 组件状态管理
const showControls = ref(false) // 控制按钮是否显示
const isEditing = ref(false) // 是否处于编辑模式
const editContent = ref('') // 编辑框内容
const copySuccess = ref(false) // 复制成功状态
const isPaused = ref(false) // 播放暂停状态
const showDeleteConfirm = ref(false) // 是否显示删除确认弹窗

// 计算属性：根据消息角色返回对应的样式类
const messageRoleClass = computed(() => ({
    'user-message': props.message.role === 'user',
    'assistant-message': props.message.role === 'assistant',
    'system-message': props.message.role === 'system'
}))

const controlRoleClass = computed(() => ({
    'user-controls': props.message.role === 'user',
    'assistant-controls': props.message.role === 'assistant',
    'system-controls': props.message.role === 'system'
}))

// 进入编辑模式
const enterEditMode = () => {
    isEditing.value = true
    editContent.value = props.message.raw_text
}

// 取消编辑
const cancelEdit = () => {
    isEditing.value = false
}

// 确认编辑内容
const confirmEdit = () => {
    const trimmedContent = editContent.value.trim()
    if (trimmedContent && trimmedContent !== props.message.raw_text) {
        emits('update-message', props.message.message_id, trimmedContent)
    }
    isEditing.value = false
}

// 处理播放/暂停切换
const handlePlayPause = () => {
    if (props.message.is_playing && !isPaused.value) {
        // 当前正在播放且未暂停 -> 暂停
        props.websocket?.sendPausePlayback()
        isPaused.value = true
    } else {
        // 当前未播放或已暂停 -> 播放
        props.websocket?.sendPlayMessage(props.message.message_id)
        isPaused.value = false
    }
}

const handlePlayStop = () => {
    props.websocket?.sendStopPlayback()
    isPaused.value = false
}

// 处理文本复制
const handleCopy = async () => {
    try {
        await navigator.clipboard.writeText(props.message.raw_text)
        copySuccess.value = true
        setTimeout(() => copySuccess.value = false, 1500) // 1.5秒后隐藏成功状态
    } catch (error) {
        console.error('复制失败:', error)
    }
}

// 处理删除音频
const handleDeleteAudio = () => {
    props.websocket?.sendDeleteAudioFiles(props.message.message_id)
}

// 显示删除确认
const handleDeleteConfirm = () => {
    showDeleteConfirm.value = true
}

// 确认删除消息
const confirmDelete = () => {
    props.websocket?.sendDeleteMessage(props.message.message_id)
    showDeleteConfirm.value = false
}

// 句子点击事件（透传）
const handleSentenceClick = (e: MouseEvent) => {
    // 句子点击处理
    const isOptionPressed = e.altKey
    const isCommandPressed = e.metaKey // macOS 上的 Command 键
    const isCtrlPressed = e.ctrlKey

    if (isOptionPressed) {
        const target = e.target as HTMLElement
        const contentElement = target.closest('.content')

        if (contentElement && (contentElement as HTMLElement).dataset) {
            const messageId = (contentElement as HTMLElement).dataset.param1
            const sentenceId = (contentElement as HTMLElement).dataset.param2

            const sentence = props.message.sentences.find(
                s => s.messageId.toString() === messageId && s.sentenceId.toString() === sentenceId
            )
            if (sentence) {
                console.log('点击的句子:', sentence)
            }
            if (isCommandPressed) {
                props.websocket?.sendPlaySentences(Number(messageId), Number(sentenceId))
            } else {
                props.websocket?.sendPlayTheSentence(Number(messageId), Number(sentenceId))
            }
        }
    }
}
</script>
