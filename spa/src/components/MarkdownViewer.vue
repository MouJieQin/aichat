<template>
    <div class="markdown-viewer-container">
        <div class="markdown-content" v-html="markdownHtml"></div>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import MarkdownIt from 'markdown-it' // 使用 markdown-it 解析 Markdown

const props = defineProps<{
    filePath: string // public目录下的文件路径，如：'/markdowns/example.md'
}>()

const markdownHtml = ref('')
const md = new MarkdownIt() // 初始化 markdown-it 实例

const fetchMarkdown = async () => {
    try {
        const response = await fetch(props.filePath)
        if (!response.ok) throw new Error(`文件加载失败: ${response.status}`)

        const markdownText = await response.text()
        markdownHtml.value = md.render(markdownText) // 使用 markdown-it 渲染 HTML
    } catch (error) {
        console.error('读取Markdown文件时出错:', error)
        markdownHtml.value = '<div class="text-red-500">无法加载Markdown内容</div>'
    }
}

onMounted(fetchMarkdown)
</script>
