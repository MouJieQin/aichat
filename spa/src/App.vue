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
      <!-- <div class="markdown-container" @click="handleSentenceClick">
        <p v-html="processed_html"></p>
      </div> -->

      <div class="chat-messages" v-for="(msg, text_id) in chatMessages" :key="text_id">
        <div class="message" :class="{ 'self': msg.isSelf }">
          <div class="markdown-container" @click="handleSentenceClick">
            <p v-html="msg.processed_html"></p>
          </div>
          <!-- <div v-for="parse_sentence in msg.parse_result" :key="parse_sentence.id">
            <p class="content hover-highlight inline-paragraph" v-html="markdownParser.render(parse_sentence.original)"
              @click="handleSentenceClick(text_id, parse_sentence.id)"></p>
          </div> -->
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
import { ref, computed, nextTick } from 'vue'
import { useWebSocket } from '@/common/websocket-client';

import MarkdownIt from 'markdown-it'
import { processMarkdown, SentenceInfo } from '@/common/markdown-processor';
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
const chatMessages = ref([])
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
  const text_id = chatMessages.value.length
  const message = {
    type: 'user_input',
    data: {
      text: inputVal.value,
      text_id: text_id,
    },
  }
  const result = processMarkdown(inputVal.value, text_id);
  chatMessages.value.push({
    processed_html: result.html,
    sentences: result.sentences,
    time: new Date(),
    isSelf: true,
  })
  webSocket.send(message)

  const message_ = {
    type: 'sentences',
    data: {
      sentences: result.sentences,
      text_id: text_id,
    },
  }
  webSocket.send(message_)
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

const handleSentenceClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  const contentElement = target.closest('.content');

  if (contentElement) {
    const textId = contentElement.dataset.param1;
    const sentenceId = contentElement.dataset.param2;

    const sentence = sentences.value.find(
      s => s.textId.toString() === textId && s.sentenceId.toString() === sentenceId
    );
    if (sentence) {
      console.log('点击的句子:', sentence);
    }
    const message = {
      type: 'click_sentence',
      data: {
        text_id: Number(textId),
        sentence_id: Number(sentenceId),
      }
    };
    webSocket.send(message)
  }
};

// 处理输入框按键事件
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    if (e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }
}

// Websocket
// 初始化 WebSocket 连接（替换为实际服务器地址）
const webSocket = useWebSocket('ws://localhost:4999/ws/aichat/0');

// 状态展示
const status = computed(() => {
  return webSocket.getStatus().value;
});

const processed_html = ref('')
const sentences = ref<SentenceInfo[]>([]);

// 监听消息（可在组件内细化处理）
webSocket.handleMessage = (message: {}) => {
  console.log("receive message:", message)
  // const message = JSON.parse(message_text);
  switch (message.type) {
    case 'ai_response':
      console.log('收到聊天消息:', message.data);
      // 可触发 Vue 响应式更新，如更新聊天列表
      const text_id = message.data.text_id
      const result = processMarkdown(message.data.response, text_id);
      chatMessages.value.push({
        processed_html: result.html,
        sentences: result.sentences,
        time: new Date(),
        isSelf: false,
      })
      const message_ = {
        type: 'sentences',
        data: {
          sentences: result.sentences,
          text_id: text_id,
        },
      }
      webSocket.send(message_)
      break;
    case 'sentences':
      console.log('系统通知:', message.data);
      // 处理通知逻辑，如弹窗提醒
      break;
    default:
      console.log('未知消息类型:', message);
  }
};

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