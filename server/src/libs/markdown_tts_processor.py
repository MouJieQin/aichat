import re
import json
from typing import List, Dict, Tuple


class MarkdownTTSProcessor:
    """处理 Markdown 文本，为 TTS 准备内容"""

    def __init__(self):
        # 定义用于清理 Markdown 格式的正则表达式模式
        self.format_patterns = [
            (r"\*\*(.*?)\*\*", r"\1"),  # 粗体
            (r"\*(.*?)\*", r"\1"),  # 斜体
            (r"~~(.*?)~~", r"\1"),  # 删除线
            (r"`(.*?)`", r"\1"),  # 行内代码
            (r"^\s*#+\s*", ""),  # 标题
            (r"^\s*[-*+]\s+", ""),  # 列表项 (修改：匹配符号后至少有一个空格)
            (r"^\s*\d+\.\s*", ""),  # 有序列表
            (r"^\s*>\s*", ""),  # 块引用
            (r"\[([^]]+)\]\([^)]+\)", r"\1"),  # 链接
            (r"!\[([^]]+)\]\([^)]+\)", r"\1"),  # 图片
            (r"^\s*---+\s*$", ""),  # 分隔线 (修改：匹配多个连字符)
            (r"^\s*```.*?```\s*$", ""),  # 代码块
        ]

        # 改进的句子分割正则表达式
        self.sentence_pattern = r"""
            (?<=[。？！！\?!\.\uff01\uff1f\uff0e])  # 匹配常见的结束标点
            \s*                                     # 可选的空白字符
            |                                       # 或者
            (?<=\n)                                 # 前一个字符是换行符
            (?:(?=^\s*([-*+]|\d+\.|\#|>))          # 下一行是列表项、标题或块引用
            |                                       # 或者
            (?=^\s*\S))                             # 下一行是非空行（忽略行首空格）
        """

    def clean_markdown(self, text: str) -> str:
        """移除 Markdown 格式字符"""
        for pattern, replacement in self.format_patterns:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text.strip()

    def split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        # 确保文本以换行符开始和结束，便于正则匹配
        processed_text = "\n" + text.strip() + "\n"

        # 使用VERBOSE和MULTILINE标志
        regex = re.compile(self.sentence_pattern, re.VERBOSE | re.MULTILINE)

        # 手动实现split逻辑，避免返回None
        sentences = []
        last_pos = 0

        for match in regex.finditer(processed_text):
            start, end = match.span()
            sentence = processed_text[last_pos:start].strip()
            if sentence:
                sentences.append(sentence)
            last_pos = end

        # 添加最后一个句子
        last_sentence = processed_text[last_pos:].strip()
        if last_sentence:
            sentences.append(last_sentence)

        return sentences

    def process(self, markdown_text: str) -> List[Dict[str, str]]:
        """处理 Markdown 文本，返回句子列表"""
        # 先分割句子，再清理每个句子
        original_sentences = self.split_into_sentences(markdown_text)

        # 构建结果列表，每个元素包含原始句子和清理后的文本
        result = []
        for i, original in enumerate(original_sentences):
            result.append(
                {
                    "id": i,
                    "original": original,
                    "cleaned": self.clean_markdown(original),
                }
            )

        return result

    def save_to_json(self, sentences: List[Dict[str, str]], filename: str) -> None:
        """将处理后的句子保存到 JSON 文件"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)
