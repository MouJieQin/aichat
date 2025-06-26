// markdownProcessor.ts
import MarkdownIt from 'markdown-it';
import { sentenceTokenizer } from 'natural'; // 或使用其他句子分割库

// 配置 MarkdownIt 解析器
const markdownParser = new MarkdownIt({
    html: true,
    breaks: true,
    linkify: true
});

// 自定义渲染器，为标题和段落添加类名
markdownParser.renderer.rules.heading_open = function (tokens, idx, options, env, self) {
    const level = tokens[idx].hLevel;
    return `<h${level} class="markdown-heading h${level}">`;
};

markdownParser.renderer.rules.paragraph_open = function (tokens, idx, options, env, self) {
    return '<p class="markdown-paragraph">';
};

// 句子处理结果接口
export interface SentenceInfo {
    text: string;
    textId: number;
    sentenceId: number;
    elementId?: string;
}

// 处理 Markdown 内容的主函数
export function processMarkdown(markdownContent: string): {
    processedHtml: string;
    sentences: SentenceInfo[];
} {
    // 1. 先渲染 Markdown 为 HTML
    let html = markdownParser.render(markdownContent);

    // 2. 创建 DOM 元素用于解析
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    // 3. 存储所有句子信息
    const sentences: SentenceInfo[] = [];

    // 4. 递归处理所有节点
    processNode(tempDiv, sentences);

    // 5. 返回处理后的 HTML 和句子信息
    return {
        processedHtml: tempDiv.innerHTML,
        sentences
    };
}

// 递归处理节点及其子节点
function processNode(node: Node, sentences: SentenceInfo[], textId: number = 0, sentenceId: number = 0): [number, number] {
    if (node.nodeType === Node.TEXT_NODE) {
        // 处理文本节点
        const text = node.textContent?.trim() || '';
        if (!text) return [textId, sentenceId];

        // 使用自然语言处理库分割句子
        const sentencesList = sentenceTokenizer.tokenize(text);

        if (sentencesList.length === 0) return [textId, sentenceId];

        // 创建包含每个句子的 span 元素
        const parent = node.parentNode;
        if (!parent) return [textId, sentenceId];

        sentencesList.forEach((sentence, index) => {
            const span = document.createElement('span');
            span.className = 'content hover-highlight';
            span.dataset.param1 = textId.toString();
            span.dataset.param2 = sentenceId.toString();
            span.textContent = sentence + (index < sentencesList.length - 1 ? ' ' : '');

            // 保存句子信息
            sentences.push({
                text: sentence,
                textId,
                sentenceId
            });

            parent.insertBefore(span, node);
            sentenceId++;
        });

        // 移除原始文本节点
        parent.removeChild(node);

        return [textId, sentenceId];
    } else if (node.nodeType === Node.ELEMENT_NODE) {
        // 处理元素节点
        const element = node as HTMLElement;

        // 处理标题元素 - 将整个标题作为一个句子
        if (element.tagName.startsWith('H') && element.classList.contains('markdown-heading')) {
            // 清空原有内容
            while (element.firstChild) {
                element.removeChild(element.firstChild);
            }

            // 获取标题文本
            const titleText = element.textContent?.trim() || '';
            if (titleText) {
                // 创建一个包含整个标题的 span
                const span = document.createElement('span');
                span.className = 'content hover-highlight';
                span.dataset.param1 = textId.toString();
                span.dataset.param2 = sentenceId.toString();
                span.textContent = titleText;

                // 保存句子信息
                sentences.push({
                    text: titleText,
                    textId,
                    sentenceId,
                    elementId: element.id || undefined
                });

                element.appendChild(span);
                sentenceId++;
            }

            // 递归处理子节点
            let currentTextId = textId;
            let currentSentenceId = sentenceId;

            let child = element.firstChild;
            while (child) {
                const nextChild = child.nextSibling;
                [currentTextId, currentSentenceId] = processNode(child, sentences, currentTextId, currentSentenceId);
                child = nextChild;
            }

            return [currentTextId + 1, currentSentenceId];
        }

        // 递归处理其他元素节点
        let currentTextId = textId;
        let currentSentenceId = sentenceId;

        let child = element.firstChild;
        while (child) {
            const nextChild = child.nextSibling;
            [currentTextId, currentSentenceId] = processNode(child, sentences, currentTextId, currentSentenceId);
            child = nextChild;
        }

        return [currentTextId, currentSentenceId];
    }

    return [textId, sentenceId];
}
