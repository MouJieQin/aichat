<template>
    <div>
        <session-item v-for="session in sessions" :key="session.path" :session="session" :webSocket="webSocket"
            @navigate="navigateTo" />
    </div>
</template>

<script lang="ts" setup>
import { defineProps, defineEmits } from 'vue'
import SessionItem from '@/components/Sidebar/SessionItem.vue'
import { WebSocketService } from '@/common/websocket-client'

const props = defineProps({
    sessions: {
        type: Array<any>,
        required: true
    },
    webSocket: {
        type: WebSocketService,
        required: true
    }
})

const emits = defineEmits([
    'navigate',
])

const navigateTo = (path: string) => {
    emits('navigate', path)
}
</script>