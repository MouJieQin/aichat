<template>
    <el-dialog v-model="visible" title="编辑对话名称" width="500px" @close="handleClose" align-center>
        <el-form>
            <el-form-item>
                <el-input v-model="title" autocomplete="off" placeholder="输入对话名称" />
            </el-form-item>
        </el-form>
        <template #footer>
            <div class="dialog-footer">
                <el-button @click="handleClose">取消</el-button>
                <el-button type="primary" @click="confirm">确定</el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import { WebSocketService } from '@/common/websocket-client'

const props = defineProps({
    visible: {
        type: Boolean,
        default: false
    },
    webSocket: {
        type: WebSocketService,
        required: true
    },
    sessionId: {
        type: Number,
        required: true
    },
    initialTitle: {
        type: String,
        default: ''
    }
})

const emits = defineEmits(['close'])

const visible = ref(props.visible)
const title = ref(props.initialTitle)

// 确认修改
const confirm = () => {
    if (title.value.trim()) {
        update_session_title()
        visible.value = false
    }
    handleClose()
}

const update_session_title = () => {
    const message = {
        type: 'update_session_title',
        data: {
            session_id: props.sessionId,
            title: title.value,
        },
    }
    console.log(message)
    props.webSocket.send(message)
}

// 关闭对话框
const handleClose = () => {
    visible.value = false
    emits('close')
}

// 监听可见性变化
watch(() => props.visible, (newVisible) => {
    visible.value = newVisible
    if (newVisible) {
        title.value = props.initialTitle
    }
})
</script>