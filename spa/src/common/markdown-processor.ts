// markdown-processor.ts
import MarkdownIt from 'markdown-it';
import { split } from 'sentence-splitter';

// 句子信息接口
export interface SentenceInfo {
    text: string;
    messageId: number;
    sentenceId: number;
    isHeading?: boolean;
}

// 处理结果接口
export interface ProcessResult {
    html: string;
    sentences: SentenceInfo[];
}

// 主处理函数
export function processMarkdown(markdownContent: string, message_id: number): ProcessResult {
    const md = new MarkdownIt();
    let html = md.render(markdownContent);
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    const sentences: SentenceInfo[] = [];

    // 递归处理节点核心逻辑（与原Vue文件完全一致）
    const walk = (node: Node, messageId: number = message_id, sentenceId: number = 0) => {
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent?.trim() || '';
            if (text) {
                const nodes = split(text).filter(n => n.type === 'Sentence');
                const parent = node.parentNode;

                // 保存所有子节点，避免在循环中修改DOM导致的问题
                const children = Array.from(parent?.childNodes || []);
                const nodeIndex = children.indexOf(node);

                // 移除原始文本节点
                parent?.removeChild(node);

                // 插入分割后的句子
                nodes.forEach((n, i) => {
                    const span = document.createElement('span');
                    span.className = 'content hover-highlight';
                    span.dataset.param1 = messageId.toString();
                    span.dataset.param2 = (sentenceId + i).toString();
                    span.textContent = n.raw;

                    sentences.push({
                        text: n.raw,
                        messageId,
                        sentenceId: sentenceId + i
                    });

                    // 在原位置插入新节点
                    parent?.insertBefore(span, children[nodeIndex + i + 1] || null);
                    
                    // 添加空格字符，保留原始空格
                    if (i < nodes.length - 1) {
                        // 检测原始文本中句子后的空格
                        const nextCharIndex = n.range[1];
                        if (nextCharIndex < text.length && text[nextCharIndex] === ' ') {
                            parent?.insertBefore(document.createTextNode(' '), children[nodeIndex + i + 2] || null);
                        }
                    }
                });

                return [messageId, sentenceId + nodes.length];
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            // 处理标题作为单个句子
            if (node.tagName.startsWith('H')) {
                const titleText = node.textContent?.trim() || '';
                if (titleText) {
                    node.innerHTML = '';
                    const span = document.createElement('span');
                    span.className = 'content hover-highlight';
                    span.dataset.param1 = messageId.toString();
                    span.dataset.param2 = sentenceId.toString();
                    span.textContent = titleText;
                    node.appendChild(span);

                    sentences.push({
                        text: titleText,
                        messageId,
                        sentenceId,
                        isHeading: true
                    });

                    return [messageId, sentenceId + 1];
                }
            }

            // 递归处理子节点
            let currentTextId = messageId;
            let currentSentenceId = sentenceId;

            Array.from(node.childNodes).forEach(child => {
                const result = walk(child, currentTextId, currentSentenceId);
                currentTextId = result[0];
                currentSentenceId = result[1];
            });

            return [currentTextId, currentSentenceId];
        }

        return [messageId, sentenceId];
    };

    walk(tempDiv);
    return {
        html: tempDiv.innerHTML,
        sentences
    };
}