<template>
    <div v-if="streaming" class="message-stream">
        <div v-if="!error" v-html="renderedContent"></div>
        <div v-else class="error-message" v-text="content"></div>
    </div>
</template>

<script lang="ts" setup>
import { defineProps, computed, watch } from 'vue'
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
