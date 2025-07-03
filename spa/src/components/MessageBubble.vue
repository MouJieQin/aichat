<template>
    <div @mouseenter="showButtons = true" @mouseleave="showButtons = false">
        <div class="message"
            :class="{ 'user': msg.role === 'user', 'assistant': msg.role === 'assistant', 'system': msg.role === 'system' }">
            <div class="markdown-container" @click="sentenceClick">
                <p v-show="!show_edit_area" v-html="msg.processed_html"></p>
            </div>
            <div class="edit-input-container">
                <el-input v-if="show_edit_area" autosize v-model="edit_input" type="textarea" />
            </div>
            <div class="time">{{ msg.time }}</div>
        </div>
        <div class="message-button-group"
            :class="{ 'user': msg.role === 'user', 'assistant': msg.role === 'assistant', 'system': msg.role === 'system' }">
            <el-button-group v-if="show_edit_area">
                <el-button :type="''" :icon="Close" text @click="show_edit_area = false" />
                <el-button :type="''" :icon="Check" text @click="handleEditConfirm" />
            </el-button-group>
            <el-button-group
                :style="{ opacity: showButtons && !show_edit_area ? '1' : '0', pointerEvents: showButtons && !show_edit_area ? 'auto' : 'none' }">
                <el-button :type="''" :icon="VideoPlay" text @click="handlePlay" v-if="showPlayButton" />
                <el-button :type="''" :icon="Edit" text @click="handleEditClick" />
                <el-button :type="''" :icon="show_copy_check ? Check : CopyDocument" text @click="handleCopyClick"
                    v-if="showCopyButton" />
                <el-button :type="''" :icon="Delete" text @click="handleDelete"/>
            </el-button-group>
        </div>
    </div>
</template>

<script setup lang="ts">
import {
    Edit,
    CopyDocument,
    Delete,
    VideoPlay,
    Close,
    Check,
} from '@element-plus/icons-vue'
import { ref } from 'vue'
const show_edit_area = ref(false)
const show_copy_check = ref(false)
const showButtons = ref(false)
const edit_input = ref('')


const handleCopyClick = () => {
    show_copy_check.value = true
    navigator.clipboard.writeText(props.msg.raw_text)
    setTimeout(() => {
        show_copy_check.value = false
    }, 1000)
}

const handleEditClick = () => {
    show_edit_area.value = true
    edit_input.value = props.msg.raw_text
}

const handleEditConfirm = () => {
    show_edit_area.value = false
    if (edit_input.value !== props.msg.raw_text) {
        props.update_message(props.msg.message_id, edit_input.value)
    }
}

const sentenceClick = (e: MouseEvent) => {
    props.handleSentenceClick(e)
}

const props = defineProps({
    msg: {
        type: Object,
        required: true,
        default: () => ({
            message_id: 0,
            raw_text: '',
            role: '',
            processed_html: '',
            time: ''
        })
    },
    handleSentenceClick: {
        type: Function,
        required: true,
    },
    update_message: {
        type: Function,
        required: true,
    },
    showPlayButton: {
        type: Boolean,
        default: false
    },
    showCopyButton: {
        type: Boolean,
        default: true
    },
    showDeleteButton: {
        type: Boolean,
        default: false
    }
})

const emits = defineEmits(['play', 'edit', 'copy', 'delete'])

const handlePlay = () => emits('play', props.msg)
const handleCopy = () => emits('copy', props.msg)
const handleDelete = () => emits('delete', props.msg)
</script>

<style scoped>
.message-button-group.user {
    max-width: clamp(300px, 80vw, 800px);
    text-align: left;
    margin-left: auto;
    margin-right: 30px;
    margin-bottom: 12px;
}

.message-button-group.assistant {
    padding-top: 10px;
    padding-right: 710px;
}

.message-button-group.system {
    padding-top: 10px;
    padding-right: 710px;
}

/* 聊天消息样式优化 */
.message {
    padding: 8px 12px;
    border-radius: 8px;
    color: #333333;
    background-blend-mode: luminosity;
    /* filter: brightness(90%); */
}

.message.system {
    max-width: clamp(300px, 80vw, 800px);
    font-size: 16px;
    line-height: 1.6;
    padding: 20px;
    margin: 0 auto;
    text-align: left;

    background-color: #E5EAF3;
    color: #333333;
}

.message.user {
    max-width: clamp(300px, 80vw, 800px);
    text-align: left;
    background-color: #d3eafd;
    margin-left: auto;
    margin-right: 30px;
    margin-bottom: 12px;
    margin-top: 12px;
}

.message.assistant {
    max-width: clamp(300px, 80vw, 800px);
    font-size: 16px;
    line-height: 1.6;
    padding: 20px;
    margin: 0 auto;
    text-align: left;

    background-color: #f5f0e6;
    color: #333333;
}

/* 基础护眼背景 */
.fatigue-reducing-bg {
    background-color: #f5f0e6;
    /* 米白色 */
    color: #333333;
    /* 深灰色文字 */
    /* 动态亮度调节 */
    background-blend-mode: luminosity;
    filter: brightness(90%);
}

/* 夜间模式 */
.night-mode {
    background-color: #222222;
    /* 深灰色 */
    color: #e0e0e0;
    /* 浅灰色文字 */
    /* 降低对比度至7:1 */
    mix-blend-mode: difference;
}

.content {
    margin-bottom: 4px;
}

.time {
    font-size: 12px;
    color: #666;
    text-align: right;
}
</style>