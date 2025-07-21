<!-- src/components/Sidebar/SessionContextMenu.vue -->
<template>
    <!-- 更多操作下拉菜单 -->
    <el-dropdown trigger="click" placement="bottom-end" :hide-on-click="hideOnClick">
        <!-- :visible-change="hideOnClick = true" -->

        <el-icon class="hover-icon" @click.stop>
            <More />
        </el-icon>
        <template #dropdown>
            <el-dropdown-menu>

                <el-dropdown-item @click="toggleTop">
                    <el-icon>
                        <lu-pin-off v-show="session.config.top" />
                        <lu-pin v-show="!session.config.top" />
                    </el-icon>
                    <span>{{ session.config.top ? '取消置顶' : '置顶' }}</span>
                </el-dropdown-item>

                <el-dropdown-item @click="openRenameDialog">
                    <div>
                        <el-icon>
                            <EditPen />
                        </el-icon>
                        <span>重命名</span>
                    </div>
                </el-dropdown-item>

                <el-dropdown-item @click="copySession">
                    <el-icon>
                        <DocumentCopy />
                    </el-icon>
                    <span>克隆会话</span>
                </el-dropdown-item>

                <el-dropdown-item @click="copySessionAndMessages">
                    <el-icon>
                        <DocumentCopy />
                    </el-icon>
                    <span>克隆会话和消息</span>
                </el-dropdown-item>

                <el-tooltip v-if="session.config.top" content="取消置顶后才能删除" placement="right" trigger="hover">
                    <div>
                        <el-dropdown-item disabled>
                            <el-icon>
                                <Delete style="color: #FF4949; opacity: 0.5;" />
                            </el-icon>
                            <span>删除</span>
                        </el-dropdown-item>
                    </div>
                </el-tooltip>
                <el-popconfirm v-else placement="right" confirm-button-text="删除" confirm-button-type="danger"
                    cancel-button-text="取消" :icon="Delete" icon-color="#FF4949" title="确定删除对话？"
                    @confirm="deleteSession">
                    <template #reference>
                        <div>
                            <el-dropdown-item @mouseenter="hideOnClick = false" @mouseleave="hideOnClick = true">
                                <el-icon>
                                    <Delete style="color: #FF4949;" />
                                </el-icon>
                                <span>删除</span>
                            </el-dropdown-item>
                        </div>
                    </template>
                </el-popconfirm>

            </el-dropdown-menu>
        </template>
    </el-dropdown>

    <RenameSessionDialog :visible="renameDialogVisible" :webSocket="webSocket" :sessionId="session.id"
        :initialTitle="session.title" @close="handleRenameDialogClose" />
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { Delete, EditPen, DocumentCopy, More } from '@element-plus/icons-vue'
import { LuPin, LuPinOff } from 'vue-icons-plus/lu'
import { WebSocketService } from '@/common/websocket-client'
import RenameSessionDialog from '@/components/Dialogs/RenameSessionDialog.vue'

const renameDialogVisible = ref(false)
const hideOnClick = ref(true)

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
}

const handleRenameDialogClose = () => {
    renameDialogVisible.value = false
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
}
</script>