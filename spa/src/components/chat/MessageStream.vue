<template>
    <div v-if="streaming" class="message-stream">
        <div v-if="!error" v-html="renderedContent"></div>
        <div v-else class="error-message" v-text="content"></div>
    </div>
</template>

<script lang="ts" setup>
import { defineProps, computed } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

const props = defineProps({
    streaming: {
        type: Boolean,
        default: false
    },
    error: {
        type: Boolean,
        default: false
    },
    content: {
        type: String,
        default: ''
    }
})

const renderedContent = computed(() => {
    return md.render(props.content)
})
</script>

<style scoped>
.message-stream {
    max-width: clamp(300px, 80vw, 800px);
    margin: 0 auto 16px;
    padding: 16px;
    background-color: #f5f0e6;
    border-radius: 8px;
    line-height: 1.6;
}

.error-message {
    color: #ff4d4f;
}
</style>