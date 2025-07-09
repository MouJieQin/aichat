<template>
    <div class="fixed-input-area">
        <div class="input-container">
            <el-input id="chat-input" v-model="inputVal" ref="inputRef" type="textarea"
                placeholder="输入对话内容（Shift + Enter 发送）" :autosize="{ minRows: 2, maxRows: 9 }"
                @input="updateCursorPosition" @keydown="handleKeyDown" @click="updateCursorPosition" />
            <div class="button-group">
                <el-button :icon="MoreFilled" text @click="$emit('open-config')" class="control-btn" />
                <el-button :icon="Microphone" :type="props.isSpeechRecognizing ? 'success' : ''" text
                    @click="toggleSpeechRecognize" class="control-btn" />
                <el-button :icon="Promotion" :type="isInputSendable ? 'primary' : 'info'" circle
                    :disabled="!isInputSendable" @click="handleSend" class="send-btn" />
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { MoreFilled, Microphone, Promotion } from '@element-plus/icons-vue'
import { ChatWebSocketService } from '@/common/chat-websocket-client'
import { mapLanguageCode } from '@/common/utils'


const props = defineProps({
    webSocket: {
        type: ChatWebSocketService,
        required: true
    },
    language: {
        type: String,
        required: true,
        default: 'zh-CN'
    },
    isSpeechRecognizing: {
        type: Boolean,
        required: true,
        default: false
    },
    sttText: {
        type: String,
        required: true,
        default: ''
    },
    sttCursorPosition: {
        type: Number,
        required: true,
        default: 0
    }
})

const emits = defineEmits<{
    (e: 'open-config'): void
    (e: 'send', text: string): void
}>()

const inputRef = ref(null)
const inputVal = ref('')
const textAreaHeight = ref(0)
const isInputSendable = ref(false)
const cursorPosition = ref(0)
const isSttChangingInputBox = ref(false)

// 处理发送事件
const handleSend = () => {
    if (!isInputSendable.value) return
    emits('send', inputVal.value)
    inputVal.value = ''
    isInputSendable.value = false
}

// 语音识别相关
const toggleSpeechRecognize = () => {
    if (props.isSpeechRecognizing) {
        props.webSocket.sendStopSpeechRecognition()
    } else {
        const lang = mapLanguageCode(props.language)
        props.webSocket.sendStartSpeechRecognition(inputVal.value, cursorPosition.value, lang)
    }
}

// 更新光标位置
const updateCursorPosition = () => {
    isInputSendable.value = inputVal.value.trim() != ""
    setTimeout(() => {
        if (inputRef.value) {
            const textarea = inputRef.value.$refs.textarea; // @ts-ignore
            if (textarea) {
                cursorPosition.value = textarea.selectionStart;
                console.log('cursor_position.value:', cursorPosition.value)
                if (!isSttChangingInputBox.value && props.isSpeechRecognizing) {
                    // if (is_speech_recognizing.value) { 
                    props.webSocket.sendUpdateCursorPosition(inputVal.value, cursorPosition.value)
                }
            }
        }
    }, 100);
}

const setCursorPosition = (position: number) => {
    nextTick(() => {
        if (inputRef.value) {
            const textarea = inputRef.value.$refs.textarea; // @ts-ignore
            if (textarea) {
                // 限制位置范围
                const validPosition = Math.max(0, Math.min(position, inputVal.value.length));
                // 设置光标位置
                textarea.focus();
                textarea.setSelectionRange(validPosition, validPosition);
                // 更新显示
                cursorPosition.value = validPosition;
                // 触发输入事件使Element UI组件同步状态
                const event = new Event('input', { bubbles: true });
                textarea.dispatchEvent(event);
            }
        }
    });
};


// 处理按键事件
const handleKeyDown = (e: KeyboardEvent) => {
    // 箭头键和Tab键更新光标位置
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Tab'].includes(e.key)) {
        updateCursorPosition()
    }

    // Shift + Enter 发送
    if (e.key === 'Enter' && e.shiftKey) {
        e.preventDefault()
        handleSend()
    }

    // Alt + Command 触发语音识别
    if (e.altKey && e.metaKey) {
        e.preventDefault()
        toggleSpeechRecognize()
    }
}

// 监听输入框高度变化
watch(inputVal, (newVal) => {
    isInputSendable.value = inputVal.value.trim() != ""
    setTimeout(() => {
        adjustFixedInputAreaPaddingTop()
    }, 100)
})

onMounted(() => {
    setTimeout(() => {
        const textarea = document.querySelector('#chat-input') as HTMLTextAreaElement;
        textAreaHeight.value = textarea.clientHeight
        document.documentElement.style.setProperty('--fixed-input-area-padding-top', textarea.clientHeight + 'px');
    }, 100)
})

watch(() => props.sttText, (newVal) => {
    if (newVal) {
        isSttChangingInputBox.value = true
        inputVal.value = newVal
        setCursorPosition(props.sttCursorPosition)
        isSttChangingInputBox.value = false
    }
})

// 调整输入框高度相关样式
const adjustFixedInputAreaPaddingTop = () => {
    const textarea = document.querySelector('#chat-input') as HTMLTextAreaElement;
    if (textarea) {
        console.log("textarea.clientHeight:", textarea.clientHeight)
        console.log("textAreaHeight.value:", textAreaHeight.value)
        if (textAreaHeight.value !== textarea.clientHeight) {
            document.documentElement.style.setProperty('--fixed-input-area-padding-top', textarea.clientHeight + 'px');
            const scrollContainer =
                document.documentElement.scrollTop > 0
                    ? document.documentElement
                    : document.body;
            const scroll_top = textarea.clientHeight - textAreaHeight.value
            scrollContainer.scrollBy({
                top: scroll_top,
                behavior: "instant"
            });
            textAreaHeight.value = textarea.clientHeight
        }
    }
}
</script>
