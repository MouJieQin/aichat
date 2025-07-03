import openai
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from libs.chat_database import ChatDatabase
from libs.log_config import logger


class OpenAIChatAPI:
    def __init__(
        self,
        ai_config: dict,
        db: ChatDatabase,
        api_key: str,
        base_url: Optional[str] = None,
    ):
        self.db = db
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.api_key = api_key
        self.base_url = base_url

        system_ai_config = ai_config[ai_config["system_ai_config"]["ai_config_name"]]
        self.system_client = openai.OpenAI(
            # 此为默认路径，您可根据业务所在地域进行配置
            base_url=system_ai_config["base_url"],
            # 从环境变量中获取您的 API Key
            api_key=system_ai_config["api_key"],
        )
        self.system_model = system_ai_config["model"]
        self.system_temperature = 0.5

    def get_messages_for_prompt(self, session_id, max_tokens=4000, max_messages=-1):
        messages = self.db.get_session_messages(session_id, max_messages)
        messages = sorted(messages, key=lambda x: x[4])  # type:ignore 按时间排序

        system_messages = []
        user_assistant_messages = []

        for msg in messages:
            msg_id, role, raw_text, _, _ = msg
            if role == "system":
                system_messages.append({"role": role, "content": raw_text})
            else:
                user_assistant_messages.append({"role": role, "content": raw_text})

        # 优先保留system消息
        prompt_messages = system_messages

        # 计算已使用的token数（简化估算）
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

    def _create_system_chat_system_prompt(self) -> str:
        return """
你的任务是根据提供的用户和AI的对话，用标题总结对话内容，并给出3个用户接下来可能的回复或会问的问题。最终输出需为纯json格式，其中包含两个键："title"用于存放对话总结标题，"suggestions"用于存放用户接下来可能的回复或问题的数组。
请先仔细阅读对话内容，为对话生成一个简洁准确的标题，不要提及用户和AI，总结对话的核心内容。然后，根据对话的主题和上下文，推测用户接下来可能会说的话或提出的问题，列出3个可能的回复或问题。回复的语言要与对话中的相同。
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
        usr_input: str,
        ai_response: str,
    ) -> Optional[str]:
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
                    "content": usr_input,
                },
                {
                    "role": "assistant",
                    "content": ai_response,
                },
            ]
        )

        prompt_messages = []
        prompt_messages.append(system_prompt)
        prompt_messages.append(
            {
                "role": "user",
                "content": json.dumps(content, ensure_ascii=False),
            }
        )
        logger.info(f"#######prompt_messages:{prompt_messages}")
        # Non-streaming:
        print("----- standard system request -----")
        completion = self.system_client.chat.completions.create(
            model=self.system_model,
            messages=prompt_messages,
            temperature=self.system_temperature,
        )
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content

    async def chat(
        self,
        session_id: int,
        user_message: str,
        parsed_text: str,
        user_message_callback_async: Callable,
        assistant_response_callback_async: Callable,
    ) -> Optional[str]:
        # 生成消息ID

        # 保存用户消息到数据库
        message_id = self.db.add_message(
            session_id=session_id,
            role="user",
            raw_text=user_message,
            parsed_text=parsed_text,
        )
        await user_message_callback_async(message_id)
        # 获取会话配置
        session = self.db.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session_id, title, create_time, ai_config_str = session
        ai_config = json.loads(ai_config_str)

        # 获取历史消息
        prompt_messages = self.get_messages_for_prompt(
            session_id, max_tokens=ai_config.get("context_max_tokens", 4000)
        )

        # 添加当前用户消息
        prompt_messages.append({"role": "user", "content": user_message})

        print("@@@@@prompt_messages:", prompt_messages)

        # 调用OpenAI API
        print("----- streaming request -----")
        stream = self.client.chat.completions.create(
            model=ai_config.get("model", "gpt-3.5-turbo"),
            messages=prompt_messages,
            temperature=ai_config.get("temperature", 0.7),
            max_tokens=ai_config.get("max_tokens", 800),
            stream=True,
        )
        ai_response = ""  # 初始化累积变量
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                ai_response += content  # 累加每个增量内容
                await assistant_response_callback_async(ai_response, True)
                print(content, end="", flush=True)  # 实时打印（可选）
        print()
        await assistant_response_callback_async(ai_response, False)
        return ai_response

    def add_assistant_message(
        self, session_id, raw_response, parsed_text
    ) -> Optional[int]:
        # 保存AI回复到数据库
        message_id = self.db.add_message(
            session_id=session_id,
            role="assistant",
            raw_text=raw_response,
            parsed_text=parsed_text,
        )
        return message_id

    def create_new_session(
        self, title: str, ai_config: Dict, system_content: str, parsed_text: str
    ) -> tuple[int, int]:

        session_id = self.db.create_session(title=title, ai_config=ai_config)

        # 添加系统消息
        if session_id is None:
            raise ValueError("Session creation failed")
        message_id = self.db.add_message(
            session_id=session_id,
            role="system",
            raw_text=system_content,
            parsed_text=parsed_text,
        )
        if message_id is None:
            raise ValueError("System prompt creation failed")
        return (session_id, message_id)

    def get_all_session_id_title(self) -> List[Dict[str, Any]]:
        return self.db.get_all_session_id_title()

    def get_session_messages(self, session_id: int, limit=100) -> Optional[list[dict]]:
        messages = self.db.get_session_messages(session_id, limit)
        messages = sorted(messages, key=lambda x: x[4])  # type:ignore 按时间排序
        return messages

    def get_session_ai_config(self, session_id: int) -> dict:
        ai_config_str = self.db.get_session_ai_config(session_id)[0]
        return json.loads(ai_config_str)

    def get_session_system_message(self, session_id: int) -> Optional[str]:
        system_message = self.db.get_session_system_messages(session_id)
        if system_message:
            return system_message[0]
        return None

    def update_session_ai_config(self, session_id: int, ai_config: dict):
        self.db.update_session_ai_config(session_id, ai_config)

    def update_session_title(self, session_id: int, title: str):
        self.db.update_session_title(session_id, title)

    def delete_session(self, session_id: int):
        self.db.delete_session_and_messages(session_id)

    def delete_message(self, message_id: int):
        self.db.delete_message(message_id)

    def update_message(
        self, message_id: int, parsed_text: str, raw_text: Optional[str] = None
    ):
        self.db.update_message(message_id, parsed_text, raw_text)

    def get_sentences(self, message_id: int) -> Optional[list[dict]]:
        parsed_text = self.db.get_parsed_text(message_id)[0]
        if parsed_text:
            return json.loads(parsed_text)["sentences"]
        return None
