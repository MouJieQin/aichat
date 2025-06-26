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
      <div class="markdown-container" @click="handleSentenceClick">
        <p v-html="test_html"></p>
      </div>

      <div class="chat-messages" v-for="(msg, text_id) in chatMessages" :key="text_id">
        <div class="message" :class="{ 'self': msg.isSelf }">
          <!-- <p v-for="parse_sentence in msg.parse_result" :key="parse_sentence.id"
            class="content hover-highlight inline-paragraph" v-html="markdownParser.render(parse_sentence.original)"
            @click="handleSentenceClick(text_id, parse_sentence.id)"></p> -->
          <div v-for="parse_sentence in msg.parse_result" :key="parse_sentence.id">
            <p class="content hover-highlight inline-paragraph" v-html="markdownParser.render(parse_sentence.original)"
              @click="handleSentenceClick(text_id, parse_sentence.id)"></p>
          </div>
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
import { processMarkdown } from '@/common/markdown-processor';
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
    type: 'text',
    data: inputVal.value,
    text_id: text_id,
  }
  webSocket.send(message)
  chatMessages.value.push({
    parse_result: {},
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


// const delegateClick = (event: MouseEvent) => {
//   const target = event.target as HTMLElement;

//   // 检查点击的元素是否有content类
//   if (target.classList.contains('content')) {
//     // 执行你想要的操作
//     const param1 = parseInt(target.dataset.param1 || '0', 10);
//     const param2 = parseInt(target.dataset.param2 || '0', 10);
//     handleSentenceClick(param1, param2);
//   }
// }

const handleSentenceClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement;

  if (target.classList.contains('content')) {
    const textId = parseInt(target.dataset.param1 || '0', 10);
    const sentenceId = parseInt(target.dataset.param2 || '0', 10);

    // 查找对应的句子信息
    const sentenceInfo = sentences.value.find(
      s => s.textId === textId && s.sentenceId === sentenceId
    );

    if (sentenceInfo) {
      console.log('点击的句子:', sentenceInfo);
      // 这里可以添加高亮或其他处理逻辑
    }
  }
};



// const handleSentenceClick = (text_id: number, sentence_id: number) => {
//   console.log("click sentence:", text_id, sentence_id)
//   const message = {
//     type: 'sentence',
//     data: {
//       "text_id": text_id,
//       "sentence_id": sentence_id,
//     }
//   }
//   webSocket.send(message)
// }

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
const webSocket = useWebSocket('ws://localhost:4999/ws/aichat/123');

// 状态展示
const status = computed(() => {
  return webSocket.getStatus().value;
});

const messageContent = ref('');
const test_html = ref('')
const sentences = ref<SentenceInfo[]>([]);

// 监听消息（可在组件内细化处理）
webSocket.handleMessage = (message: {}) => {
  console.log("receive message:", message)
  // const message = JSON.parse(message_text);
  switch (message.type) {
    case 'parse_result':
      console.log('收到聊天消息:', message.data);
      // 可触发 Vue 响应式更新，如更新聊天列表
      const text_id = message.data.text_id
      chatMessages.value[text_id].parse_result = message.data.result
      // console.log(markdownParser.render(message.data.result[0].original))
      //       const markdownContent = `
      // 素晴らしい質問ですね！あなたの問いは、プラトンの『国家』の核心に触れるものであり、特に「気概」と「節制」の役割や、それらが理性と欲望の間でどのように機能するかについて深く考えさせられます。それぞれを整理しながら、関係性を明確にしていきましょう。

      // ---

      // ### **1. 気概はどちらに傾いているのか？**
      // 気概（トューモス）は、理性と欲望の間で「中間的な存在」として機能しますが、プラトンは気概が**理性に従うべき**だと考えています。

      // #### **理性に従う気概**
      // - 理性が「国家や個人にとって何が善であるか」を判断し、気概がそれを実行に移す役割を果たします。
      // - 欲望に傾いた気概は、盲目的な怒りや衝動として現れる可能性があり、理性に従わない場合には調和が崩れてしまいます。
      //       `
      const markdownContent = `
# 哲学与心理学

哲学思考常常涉及对人性的深入探究。心理学则通过科学方法研究人类行为和心理过程。
这两个领域虽然方法不同，但都致力于理解人类的本质。

## 理性与情感

理性决策通常被认为是基于逻辑和事实的。
然而，情感在人类决策过程中也扮演着重要角色。
`;

      // test_html.value = test_html.value.replace(/<li>/g, '<li class="content hover-highlight" data-param1="3" data-param2="0">')
      // console.log(test_html.value
      const result = processMarkdown(markdownContent);
      test_html.value = result.processedHtml;
      sentences.value = result.sentences;

      console.log('处理后的句子:', sentences.value);
      console.log('处理后的html:', test_html.value);

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