import openai
import json
import ast
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Union
from libs.chat_database import ChatDatabase
from libs.log_config import logger
import time


class OpenAIChatAPI:
    def __init__(
        self,
        ai_config: dict,
        db: ChatDatabase,
    ):
        self.db = db
        system_ai_config = ai_config[ai_config["system_ai_config"]["ai_config_name"]]
        self.system_client = openai.OpenAI(
            base_url=system_ai_config["base_url"],
            api_key=system_ai_config["api_key"],
        )
        self.system_model = system_ai_config["model"]
        self.system_temperature = 0.5
        self._stop_response = False

    @staticmethod
    def unescape_string(s: str) -> Optional[str]:
        """安全地反转义字符串，处理各种转义字符"""
        try:
            return ast.literal_eval(f'"{s}"')
        except Exception:
            return None

    def stop_response(self) -> None:
        """停止当前的响应"""
        self._stop_response = True

    def _create_system_prompt(
        self, user_system_prompt: str, with_system_prompt: bool
    ) -> str:
        """创建系统提示词，根据是否需要系统提示词包装"""
        if not with_system_prompt:
            return user_system_prompt

        return f"""
        用户设置：{user_system_prompt}
        你的回复使用的语言种类要参考上下文对话内容(本条消息使用了中文，但不作为上下文语种参考依据)，并且严格按照以下格式进行回复（请严格保持此纯json格式，不要添加额外文本）：
        {{
            "response": "针对用户问题的详细回答",
            "title": "问题的简短标题",
            "suggestions": ["用户可能接下来问的问题或回应1", "用户可能接下来问的问题或回应2", "用户可能接下来问的问题或回应3"],
        }}
        """

    def get_messages_for_prompt(
        self,
        with_system_prompt: bool,
        session_id: int,
        max_tokens: int = 4000,
        max_messages: int = 100,
    ) -> List[Dict[str, str]]:
        """获取用于提示的消息列表，考虑token限制和消息顺序"""
        messages = self.db.get_session_messages(session_id, max_messages)
        messages = sorted(messages, key=lambda x: x["timestamp"])

        system_messages = []
        user_assistant_messages = []

        # 分离系统消息和用户/助手消息
        has_system_prompt = False
        for msg in messages:
            role = msg["role"]
            raw_text = msg["raw_text"]
            if role == "system":
                has_system_prompt = True
                system_messages.append(
                    {
                        "role": role,
                        "content": self._create_system_prompt(
                            raw_text, with_system_prompt
                        ),
                    }
                )
            else:
                user_assistant_messages.append({"role": role, "content": raw_text})

        # 如果没有系统消息，添加默认系统提示
        if not has_system_prompt:
            system_prompt = self.get_session_system_message(session_id)
            system_messages.append(
                {
                    "role": "system",
                    "content": self._create_system_prompt(
                        system_prompt or "", with_system_prompt
                    ),
                }
            )
        # 构建最终提示消息，考虑token限制
        prompt_messages = system_messages
        used_tokens = sum(len(msg["content"]) // 4 for msg in prompt_messages)

        # 从最新消息开始添加，直到达到token限制
        reversed_messages = user_assistant_messages[::-1]
        messages_to_send = []

        for msg in reversed_messages:
            msg_tokens = len(msg["content"]) // 4
            if used_tokens + msg_tokens > max_tokens:
                break
            messages_to_send.append(msg)
            used_tokens += msg_tokens

        # 恢复正确顺序
        messages_to_send = messages_to_send[::-1]

        return prompt_messages + messages_to_send
        # return messages_to_send + prompt_messages

    def _create_system_chat_system_prompt(self) -> str:
        """创建用于系统聊天的系统提示词"""
        return """
        你的任务是根据提供的用户和AI的对话，用标题总结对话内容，并给出3个用户接下来可能的回复或会问的问题。最终输出需为纯json格式，其中包含两个键："title"用于存放对话总结标题，"suggestions"用于存放用户接下来可能的回复或问题的数组。
        请先仔细阅读对话内容，为对话生成一个简洁准确的标题，不要提及用户和AI，总结对话的核心内容。然后，根据对话的主题和上下文，推测用户接下来可能会说的话或提出的问题，列出3个可能的回复或问题。标题和建议所使用的语言要与要总结的对话内容中的相同。
        最终输出格式如下：
        {
            "title": "对话总结标题",
            "suggestions": [
                "用户可能的回复或问题1",
                "用户可能的回复或问题2",
                "用户可能的回复或问题3"
            ]
        }
        """

    def system_chat(
        self,
        system_prompt_content: Optional[str],
        user_input: str,
        ai_response: str,
    ) -> Optional[str]:
        """分析对话内容，生成标题和建议"""
        system_prompt = {
            "role": "system",
            "content": self._create_system_chat_system_prompt(),
        }

        content = []
        if system_prompt_content:
            content.append(
                {
                    "role": "system",
                    "content": system_prompt_content,
                }
            )
        content.extend(
            [
                {
                    "role": "user",
                    "content": user_input,
                },
                {
                    "role": "assistant",
                    "content": ai_response,
                },
            ]
        )

        prompt_messages = [
            system_prompt,
            {
                "role": "user",
                "content": json.dumps(content, ensure_ascii=False),
            },
        ]

        logger.info(f"#######系统分析提示:{prompt_messages}")

        # 发送请求到系统模型
        logger.info("----- 系统分析请求 -----")
        completion = self.system_client.chat.completions.create(
            model=self.system_model,
            messages=prompt_messages,  # type: ignore
            temperature=self.system_temperature,
        )

        logger.info(completion.choices[0].message.content)
        return completion.choices[0].message.content

    async def chat(
        self,
        with_system_prompt: bool,
        session_id: int,
        user_message: str,
        parsed_text: str,
        user_message_callback_async: Callable,
        assistant_response_callback_async: Callable,
    ) -> Dict:
        """处理用户聊天请求，支持流式响应"""
        # 保存用户消息到数据库
        message_id = self.db.add_message(
            session_id=session_id,
            role="user",
            raw_text=user_message,
            parsed_text=parsed_text,
        )
        await user_message_callback_async(message_id)

        # 获取会话配置
        ai_config = self.get_session_ai_config(session_id)

        # 获取历史消息用于提示
        prompt_messages = self.get_messages_for_prompt(
            with_system_prompt,
            session_id,
            max_tokens=ai_config.get("context_max_tokens", 4000),
            max_messages=ai_config.get("max_messages", 10),
        )

        # 添加格式控制消息
        prompt_messages.append(
            {
                "role": "system",
                "content": "请注意回复格式要严格遵循系统设置的纯json格式，并且使用的语言种类要参考上下文对话内容。",
            }
        )

        logger.info(f"@@@@@提示消息:{prompt_messages}")

        # 创建OpenAI客户端并发送请求
        client = openai.OpenAI(
            api_key=ai_config["api_key"], base_url=ai_config["base_url"]
        )

        logger.info("----- 流式请求 -----")
        self._stop_response = False
        # 发送流式请求
        response_stream = client.chat.completions.create(  # type: ignore
            model=ai_config.get("model", "gpt-3.5-turbo"),
            messages=prompt_messages,  # type: ignore
            temperature=ai_config.get("temperature", 0.7),
            max_tokens=ai_config.get("max_tokens", 800),
            stream=True,
        )

        # 根据是否需要系统提示词，采用不同的处理方式
        if with_system_prompt:
            return await self._process_stream_response(
                response_stream, assistant_response_callback_async
            )
        else:
            return await self._process_simple_stream(
                response_stream, assistant_response_callback_async
            )

    async def _process_simple_stream(
        self,
        response_stream: openai.Stream,
        callback: Callable,
    ) -> dict:
        """处理简单流式响应（非JSON格式）"""
        full_response = ""
        for chunk in response_stream:
            if self._stop_response:
                logger.info("流式响应已停止")
                break
            # 检查是否有内容
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                await callback(full_response, True)
                print(content, end="", flush=True)

        print()
        await callback(full_response, False)
        return {"response": full_response}

    async def _process_stream_response(
        self,
        response_stream: openai.Stream,
        callback: Callable,
    ) -> dict:
        """处理JSON格式的流式响应，提取response字段内容"""
        full_response = ""
        response_content = ""
        in_response_field = False
        response_ended = False
        escaped = False

        for chunk in response_stream:
            if self._stop_response:
                logger.info("流式响应已停止")
                break
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content

                if response_ended:
                    continue

                # 状态机解析"response"字段内容
                if not in_response_field:
                    response_pos = full_response.find('"response": "')
                    if response_pos != -1:
                        in_response_field = True
                        response_start = response_pos + len('"response": "')
                        content = full_response[response_start:]
                        clean_content, escaped, response_ended = (
                            self._parse_stream_content(content, escaped, response_ended)
                        )

                        if clean_content:
                            response_content += clean_content
                            print(clean_content, end="", flush=True)
                            await self._send_response_chunk(response_content, callback)
                else:
                    clean_content, escaped, response_ended = self._parse_stream_content(
                        content, escaped, response_ended
                    )
                    if clean_content:
                        print(clean_content, end="", flush=True)
                        response_content += clean_content
                        await self._send_response_chunk(response_content, callback)

        logger.info("-----------------------------------------------")
        logger.info(f"完整响应: {full_response}")
        await callback(response_content, False)

        # 解析完整响应JSON
        return self._parse_response_json(full_response, response_content)

    def _parse_stream_content(
        self, content: str, escaped: bool, response_ended: bool
    ) -> tuple[str, bool, bool]:
        """解析流式响应内容，处理转义字符和引号"""
        clean_content = ""
        for char in content:
            if escaped:
                clean_content += char
                escaped = False
            elif char == "\\":
                clean_content += char
                escaped = True
            elif char == '"':
                response_ended = True
                break
            else:
                clean_content += char
        return clean_content, escaped, response_ended

    async def _send_response_chunk(self, content: str, callback: Callable) -> None:
        """发送响应块到回调函数"""
        unescaped = self.unescape_string(content)
        if unescaped:
            await callback(unescaped, True)

    def _parse_response_json(self, full_response: str, response_content: str) -> dict:
        """解析响应JSON，处理解析失败的情况"""
        try:
            return json.loads(full_response)
        except json.JSONDecodeError:
            logger.warning("解析响应JSON失败，使用回退方案")
            return {
                "response": response_content,
                "title": "问题总结",
                "suggestions": [
                    "能否提供更多细节？",
                    "还有其他补充信息吗？",
                    "请解释得更清楚一些",
                ],
            }

    # 会话管理方法
    def create_new_session(
        self, title: str, ai_config: Dict, system_content: str, parsed_text: str
    ) -> tuple[int, int]:
        """创建新会话并返回会话ID和消息ID"""
        session_id = self.db.create_session(title=title, ai_config=ai_config)
        if session_id is None:
            raise ValueError("会话创建失败")

        message_id = self.db.add_message(
            session_id=session_id,
            role="system",
            raw_text=system_content,
            parsed_text=parsed_text,
        )
        if message_id is None:
            raise ValueError("系统提示创建失败")

        return (session_id, message_id)

    def copy_session(self, session_id: int) -> Optional[int]:
        """复制会话，只复制会话元数据"""
        new_session_id = self.db.copy_session(session_id)
        if new_session_id:
            self.db.copy_session_system_message(session_id, new_session_id)
        return new_session_id

    def copy_session_and_messages(self, session_id: int) -> Optional[int]:
        """复制会话及其所有消息"""
        return self.db.copy_session_and_messages(session_id)

    def get_all_session_id_title_config(self) -> List[Any]:
        """获取所有会话的ID、标题和配置"""
        return self.db.get_all_session_id_title_config()

    def get_session_title(self, session_id: int) -> Optional[str]:
        """获取会话标题"""
        return self.db.get_session_title(session_id)

    def get_session_messages(
        self, session_id: int, limit: int = -1
    ) -> Optional[List[Dict]]:
        """获取会话消息"""
        messages = self.db.get_session_messages(session_id, limit)
        return sorted(messages, key=lambda x: x["timestamp"]) if messages else []

    def get_session_ai_config(self, session_id: int) -> dict:
        """获取会话AI配置"""
        return self.db.get_session_ai_config(session_id) or {}

    def get_session_ai_avatar_url(self, session_id: int) -> Optional[str]:
        """获取会话AI头像"""
        config = self.get_session_ai_config(session_id)
        return config.get("ai_avatar_url", "")

    def is_session_exist(self, session_id: int) -> bool:
        """检查会话是否存在"""
        return self.db.is_session_exist(session_id)

    def get_session_system_message(self, session_id: int) -> Optional[str]:
        """获取会话系统消息"""
        return self.db.get_session_system_message(session_id)

    def add_assistant_message(
        self, session_id: int, raw_response: str, parsed_text: str
    ) -> Optional[int]:
        """添加助手消息"""
        # 保存AI回复到数据库
        return self.db.add_message(session_id, "assistant", raw_response, parsed_text)

    def update_session_ai_config(self, session_id: int, ai_config: dict) -> None:
        """更新会话AI配置"""
        self.db.update_session_ai_config(session_id, ai_config)

    def update_session_title(self, session_id: int, title: str) -> None:
        """更新会话标题"""
        self.db.update_session_title(session_id, title)

    def update_session_property(self, session_id: int, key: str, value: Any) -> None:
        """更新会话属性"""
        ai_config = self.get_session_ai_config(session_id)
        ai_config[key] = value
        self.update_session_ai_config(session_id, ai_config)

    def update_session_top(self, session_id: int, top: bool) -> None:
        """更新会话置顶状态"""
        self.update_session_property(session_id, "top", top)

    def update_session_auto_gen_title(
        self, session_id: int, auto_gen_title: bool
    ) -> None:
        """更新会话自动生成标题设置"""
        self.update_session_property(session_id, "auto_gen_title", auto_gen_title)

    def update_session_suggestions(
        self, session_id: int, suggestions: List[str]
    ) -> None:
        """更新会话建议"""
        self.update_session_property(session_id, "suggestions", suggestions)

    def update_session_last_active_time(
        self, session_id: int, last_active_time: float = time.time()
    ) -> None:
        """更新会话最后活动时间"""
        self.update_session_property(session_id, "last_active_time", last_active_time)

    def update_session_ai_avatar_url(self, session_id: int, avatar_url: str) -> None:
        """更新会话AI头像"""
        self.update_session_property(session_id, "ai_avatar_url", avatar_url)

    def delete_session(self, session_id: int) -> None:
        """删除会话及其所有消息"""
        self.db.delete_session_and_messages(session_id)

    def delete_message(self, message_id: int) -> None:
        """删除消息"""
        self.db.delete_message(message_id)

    def update_message(
        self, message_id: int, parsed_text: str, raw_text: Optional[str] = None
    ) -> None:
        """更新消息内容"""
        self.db.update_message(message_id, parsed_text, raw_text)

    def get_sentences(self, message_id: int) -> Optional[List[Dict]]:
        """获取消息的句子列表"""
        parsed_text = self.db.get_parsed_text(message_id)
        if parsed_text:
            try:
                return json.loads(parsed_text)["sentences"]
            except (json.JSONDecodeError, KeyError):
                return None
        return None
