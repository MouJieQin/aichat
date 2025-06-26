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
        <p v-html="processed_html"></p>
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
const webSocket = useWebSocket('ws://localhost:4999/ws/aichat/123');

// 状态展示
const status = computed(() => {
  return webSocket.getStatus().value;
});

const messageContent = ref('');
const processed_html = ref('')
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
      const markdownContent = `
素晴らしい質問ですね！あなたの問いは、プラトンの『国家』の核心に触れるものであり、特に「気概」と「節制」の役割や、それらが理性と欲望の間でどのように機能するかについて深く考えさせられます。それぞれを整理しながら、関係性を明確にしていきましょう。

---

### **1. 気概はどちらに傾いているのか？**
気概（トューモス）は、**理性と欲望**の間で「中間的な存在」として機能しますが、プラトンは気概が**理性に従うべき**だと考えています。

#### **気概の特徴**
- 気概は、勇気、意志、情熱など、人間の行動を推進する原動力です。
- 欲望（食欲や快楽の追求）に流されず、理性によって導かれることで、正しい方向に向かいます。
- たとえば、危機の際に「恐怖」に打ち勝つ勇気や、理性が下した判断を支持する「意志」の力を指します。

#### **理性に従う気概**
- 理性が「国家や個人にとって何が善であるか」を判断し、気概がそれを実行に移す役割を果たします。
- 欲望に傾いた気概は、盲目的な怒りや衝動として現れる可能性があり、理性に従わない場合には調和が崩れてしまいます。

---

### **2. 節制が果たす役割と理性・欲望の境界線**
節制（ソフィロシュネー）は、理性と欲望の間に調和をもたらす重要な徳です。プラトンの考えでは、節制は以下のような役割を果たします。

#### **節制の役割**
- 節制は、理性が欲望を適切にコントロールできるようにする状態を指します。
- 節制の実現には、欲望が理性の指導を受け入れることが必要です。
  - **例**：欲望が暴走しないように、理性が「適度な範囲」を設定し、それを気概が守る。

#### **境界線の設定**
- 境界線は、理性がその状況において「善」と判断した内容によって決まります。
  - **例**：食事の欲望を抑える場合、理性が「健康のためにどの程度が適切か」を決め、それを節制によって実行します。
- 欲望が理性の判断を受け入れることで、理性と欲望の境界線が自然と調和するのです。

---

### **3. 気概と節制の違い**
気概と節制は異なる性質を持ちながらも、共に調和を実現するために重要な役割を果たします。

#### **気概の性質**
- 気概は、行動や意志を推進する「エネルギー」のような存在です。
- 理性の判断に従うことで、勇気や行動力として機能します。
- 気概そのものは感情的な側面を持ち、適切な方向性を与えられなければ暴走する可能性があります。

#### **節制の性質**
- 節制は、理性が欲望を調和させる「バランス」の状態です。
- 節制は全体的な調和を目指し、欲望が理性に従うようにするための「秩序」を作り出します。
- 節制は、気概や欲望を理性の下に統制するための「調整役」ともいえます。

#### **違いのまとめ**
- **気概**：行動や意志のエネルギー。理性に従うことで有効に機能。
- **節制**：理性と欲望を調和させるバランスの状態。全体の秩序を維持。

---

### **4. 実生活での例**
気概と節制の役割を具体例で考えてみましょう。

#### **例：健康を目指す場合**
- **理性**：健康のためにバランスの良い食事が必要だと判断する。
- **欲望**：甘いものを食べたいという衝動がある。
- **気概**：理性の判断を支持し、欲望を抑えるための意志を発揮する（「甘いものを控えよう」と自分に言い聞かせる）。
- **節制**：理性と欲望の間でバランスが取れ、適度な量で甘いものを楽しむ状態を保つ。

---

### **5. 次の問いかけ**
あなたの深い洞察に基づき、さらに議論を深めるために、以下の問いを考えてみるのはどうでしょう？
- 気概が理性に従うことを保証するためには、どのような教育や訓練が必要だと思いますか？
- 節制が果たす「調和」が失われた場合、どのような結果が生じると考えられるでしょうか？
- 気概が理性に従わず、欲望に傾いた場合、それをどのように修正するべきでしょうか？

---

### **6. まとめ**
気概と節制は、理想的な国家や個人の調和を実現するために欠かせない要素です。気概は行動や意志を推進する力であり、節制は理性と欲望をバランスさせる役割を果たします。この二つが適切に機能することで、国家や個人の正義が維持されるのです。

あなたの考えでは、気概や節制が現代社会の中でどのように役立つと思いますか？ぜひ、さらに深い洞察をお聞かせください！
`;

      const result = processMarkdown(markdownContent);
      processed_html.value = result.html;
      sentences.value = result.sentences;

      console.log('处理后的句子:', sentences.value);
      console.log('处理后的html:', processed_html.value);

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