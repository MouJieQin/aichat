<!-- src/components/Sidebar/SessionContextMenu.vue -->
<template>
    <el-menu :collapse="false">
        <el-menu-item index="top" @click="toggleTop">
            <div>
                <el-icon>
                    <lu-pin-off v-show="session.config.top" />
                    <lu-pin v-show="!session.config.top" />
                </el-icon>
                <span>{{ session.config.top ? '取消置顶' : '置顶' }}</span>
            </div>
        </el-menu-item>

        <el-menu-item index="rename" @click="openRenameDialog">
            <div>
                <el-icon>
                    <EditPen />
                </el-icon>
                <span>重命名</span>
            </div>
        </el-menu-item>

        <el-menu-item index="copy_session" @click="copySession">
            <div>
                <el-icon>
                    <DocumentCopy />
                </el-icon>
                <span>克隆会话</span>
            </div>
        </el-menu-item>

        <el-menu-item index="copy_session_and_message" @click="copySessionAndMessages">
            <div>
                <el-icon>
                    <DocumentCopy />
                </el-icon>
                <span>克隆会话和消息</span>
            </div>
        </el-menu-item>

        <el-tooltip v-if="session.config.top" class="box-item" content="取消置顶后才能删除" placement="right">
            <el-menu-item index="delete_session" disabled>
                <div>
                    <el-icon>
                        <Delete style="color: #FF4949;" />
                    </el-icon>
                    <span>删除</span>
                </div>
            </el-menu-item>
        </el-tooltip>

        <el-popconfirm v-else placement="right" confirm-button-text="删除" confirm-button-type="danger"
            cancel-button-text="取消" :icon="Delete" icon-color="#FF4949" title="确定删除对话？" @confirm="deleteSession">
            <template #reference>
                <el-menu-item index="delete_session">
                    <div>
                        <el-icon>
                            <Delete style="color: #FF4949;" />
                        </el-icon>
                        <span>删除</span>
                    </div>
                </el-menu-item>
            </template>
        </el-popconfirm>
    </el-menu>
    <RenameSessionDialog :visible="renameDialogVisible" :webSocket="webSocket" :sessionId="session.id"
        :initialTitle="session.title" @close="handleRenameDialogClose" />
</template>

<script lang="ts" setup>
import { defineProps, defineEmits, ref, watch } from 'vue'
import { Delete, EditPen, DocumentCopy, WarningFilled } from '@element-plus/icons-vue'
import { LuPin, LuPinOff } from 'vue-icons-plus/lu'
import { WebSocketService } from '@/common/websocket-client'
import RenameSessionDialog from '@/components/Dialogs/RenameSessionDialog.vue'

const renameDialogVisible = ref(false)

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
    'closePopover'
])

// 切换置顶状态
const toggleTop = () => {
    const message = {
        type: 'update_session_top',
        data: {
            session_id: props.session.id,
            top: !props.session.config.top,
        },
    }
    props.webSocket.send(message)
    emits('closePopover')
}

const handleRenameDialogClose = () => {
    renameDialogVisible.value = false
    emits('closePopover')
}

// 打开重命名对话框
const openRenameDialog = () => {
    renameDialogVisible.value = true
}

// 复制会话
const copySession = () => {
    const message = {
        type: 'copy_session',
        data: {
            session_id: props.session.id,
        },
    }
    props.webSocket.send(message)
    emits('closePopover')
}

// 复制会话和消息
const copySessionAndMessages = () => {
    const message = {
        type: 'copy_session_and_message',
        data: {
            session_id: props.session.id,
        },
    }
    props.webSocket.send(message)
    emits('closePopover')
}

// 删除会话
const deleteSession = () => {
    const message = {
        type: 'delete_session',
        data: {
            session_id: props.session.id,
        },
    }
    props.webSocket.send(message)
    emits('closePopover')
}
</script>