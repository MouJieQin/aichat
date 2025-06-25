<template>
  <div class="app-container">
    <!-- 侧边栏区域 -->
    <div class="sidebar">
      <el-radio-group v-model="isCollapse" style="margin-bottom: 20px">
        <el-radio-button :value="false">expand</el-radio-button>
        <el-radio-button :value="true">collapse</el-radio-button>
      </el-radio-group>
      <el-menu default-active="2" class="el-menu-vertical-demo" :collapse="isCollapse" @open="handleOpen"
        @close="handleClose">
        <!-- 其他一级菜单 -->
        <el-sub-menu index="1">
          <template #title>
            <el-icon>
              <location />
            </el-icon>
            <span>Navigator One</span>
          </template>
          <!-- 子菜单内容 -->
        </el-sub-menu>

        <!-- 历史对话一级标题及二级菜单 -->
        <el-sub-menu index="history">
          <template #title>
            <el-icon><icon-menu /></el-icon>
            <span>历史对话</span>
          </template>
          <el-menu-item v-for="(item, index) in historyDialogs" :key="index" :index="`history-${index}`">
            {{ item }}
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>

    <!-- 聊天内容区域 -->
    <div class="chat-container">
      <!-- 聊天消息列表 -->
      <div class="chat-messages" v-for="(msg, idx) in chatMessages" :key="idx">
        <div class="message" :class="{ 'self': msg.isSelf }">
          <p class="content" v-html="markdownParser.render(msg.text)"></p>
          <div class="time">{{ formatTime(msg.time) }}</div>
        </div>
      </div>

      <!-- 输入区域，使用 Element Plus 的 ElInput 多行模式 -->
      <div class="input-area">
        <el-input v-model="inputVal" type="textarea" placeholder="输入对话内容（Shift + Enter 换行，Enter 发送）"
          :autosize="{ minRows: 2, maxRows: 4 }" @keydown="handleKeyDown" />
        <el-button type="primary" @click="sendMessage">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import {
  Document,
  Menu as IconMenu,
  Location,
  Setting,
} from '@element-plus/icons-vue'

const markdownParser = new MarkdownIt()
const isCollapse = ref(true)
const handleOpen = (key: string, keyPath: string[]) => {
  console.log(key, keyPath)
}
const handleClose = (key: string, keyPath: string[]) => {
  console.log(key, keyPath)
}

// 模拟聊天数据
const chatMessages = ref([
  { text: '你好，我是AI助手', time: new Date(), isSelf: false },
  { text: '很高兴为你服务', time: new Date(), isSelf: false },
  ...Array.from({ length: 50 }, (_, i) => ({
    text: `消息${i + 1}`,
    time: new Date(),
    isSelf: i % 2 === 0,
  })),
])
const inputVal = ref('')

// 历史对话二级菜单数据
const historyDialogs = ref([
  '历史对话1', '历史对话2', '历史对话3', '历史对话4', '历史对话5',
  '历史对话6', '历史对话7', '历史对话8', '历史对话9', '历史对话10',
  '历史对话11', '历史对话12', '历史对话13', '历史对话14', '历史对话1', '历史对话2', '历史对话3', '历史对话4', '历史对话5',
  '历史对话6', '历史对话7', '历史对话8', '历史对话9', '历史对话10',
  '历史对话11', '历史对话12', '历史对话13', '历史对话14',
])

// 发送消息方法
const sendMessage = () => {
  if (!inputVal.value.trim()) return
  chatMessages.value.push({
    text: inputVal.value,
    time: new Date(),
    isSelf: true,
  })
  inputVal.value = ''
  // 滚动到底部
  nextTick(() => {
    const scrollContainer = document.querySelector('.chat-container') as HTMLElement
    scrollContainer.scrollTop = scrollContainer.scrollHeight
  })
}

// 格式化时间
const formatTime = (time: Date) => {
  return (
    time.getHours().toString().padStart(2, '0') + ':' +
    time.getMinutes().toString().padStart(2, '0') + ':' +
    time.getSeconds().toString().padStart(2, '0')
  )
}

// 处理输入框按键事件
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    if (e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
}
</script>

<style scoped>
/* 整体布局 */
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: 200px;
  border-right: 1px solid #e6e6e6;
  padding: 10px;
  box-sizing: border-box;
  /* 修复滚动问题：确保内容超出时可滚动 */
  overflow-y: auto;
  /* 让侧边栏高度适应视口 */
  max-height: 100vh;
}

/* 聊天内容区域 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
  /* 优化字体显示：设置浅色文字 */
  color: #fff;
}

/* 聊天消息样式优化 */
.message {
  max-width: 60%;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 6px;
  /* 确保不同背景色下文字清晰 */
  color: #000;
}

.message.self {
  background-color: #d3eafd;
  margin-left: auto;
}

.message:not(.self) {
  background-color: #f1f1f1;
  margin-right: auto;
}

.content {
  margin-bottom: 4px;
}

.time {
  font-size: 12px;
  color: #666;
  text-align: right;
}

/* 输入区域样式 */
.input-area {
  display: flex;
  gap: 10px;
  margin-top: auto;
  align-items: flex-end;
}

.input-area el-input {
  flex: 1;
}
</style>