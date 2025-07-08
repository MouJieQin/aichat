<template>
    <div class="input-container">
        <el-input id="chat-input" v-model="value" ref="inputRef" type="textarea" placeholder="输入对话内容（Shift + Enter 发送）"
            :autosize="{ minRows: 2, maxRows: 9 }" @input="handleInput" @keydown="handleKeyDown"
            @click="updateCursorPosition" />
        <div class="button-group">
            <el-button :icon="MoreFilled" text @click="$emit('open-config')" class="control-btn" />
            <el-button :icon="Microphone" :type="isRecognizing ? 'success' : ''" text @click="$emit('toggle-recognize')"
                class="control-btn" />
            <el-button :icon="Promotion" type="primary" circle :disabled="!canSend" @click="$emit('send')"
                class="send-btn" />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { defineProps, defineEmits, ref, watch } from 'vue'
import { MoreFilled, Microphone, Promotion } from '@element-plus/icons-vue'

const props = defineProps({
    value: {
        type: String,
        default: ''
    },
    canSend: {
        type: Boolean,
        default: false
    },
    isRecognizing: {
        type: Boolean,
        default: false
    }
})

const emits = defineEmits([
    'input',
    'send',
    'toggle-recognize',
    'open-config'
])

const inputRef = ref(null)
const cursorPosition = ref(0)

// 处理输入变化
const handleInput = (value: string) => {
    emits('input', value)
}

// 更新光标位置
const updateCursorPosition = () => {
    const textarea = inputRef.value?.$refs.textarea
    if (textarea) {
        cursorPosition.value = textarea.selectionStart
    }
}

// 处理按键事件
const handleKeyDown = (e: KeyboardEvent) => {
    // 箭头键和Tab键更新光标位置
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Tab'].includes(e.key)) {
        updateCursorPosition()
    }

    // Shift + Enter 发送
    if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault()
        emits('send')
    }

    // Alt + Command 触发语音识别
    if (e.altKey && e.metaKey) {
        e.preventDefault()
        emits('toggle-recognize')
    }
}

// 监听输入框高度变化
watch(
    () => props.value,
    () => {
        adjustInputHeight()
    }
)

// 调整输入框高度相关样式
const adjustInputHeight = () => {
    const textarea = document.querySelector('#chat-input') as HTMLTextAreaElement
    if (textarea) {
        document.documentElement.style.setProperty(
            '--input-height',
            `${textarea.clientHeight}px`
        )
    }
}
</script>

<style scoped>
.input-container {
    position: relative;
    width: 100%;
    max-width: clamp(300px, 80vw, 800px);
    margin: 0 auto;
}

.button-group {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 8px;
}

.control-btn {
    font-size: 20px;
    width: 40px;
    height: 40px;
}

.send-btn {
    width: 40px;
    height: 40px;
}
</style>