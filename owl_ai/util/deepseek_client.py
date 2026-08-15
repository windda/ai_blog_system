# -*- coding: utf-8 -*-
"""
DeepSeek API 客户端工具类。

基于 OpenAI 兼容接口，使用 requests 调用 DeepSeek API；
支持流式 SSE 返回、超时控制与重试机制。

环境配置（.env）：
    DEEPSEEK_API_KEY=sk-xxxxx
    DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
    DEEPSEEK_MODEL=deepseek-chat
    DEEPSEEK_SYSTEM_PROMPT=你是一个有帮助的AI助手
"""

import os
import json
import time
import traceback
import requests


class DeepSeekClient:
    """DeepSeek API 客户端"""

    # 从环境变量读取配置
    API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    _raw_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    # 模型名称校验：不合法自动降级 flash
    _SUPPORTED_MODELS = {"deepseek-chat", "deepseek-flash", "deepseek-v4-flash", "deepseek-coder"}
    MODEL = _raw_model if _raw_model in _SUPPORTED_MODELS else "deepseek-flash"
    SYSTEM_PROMPT = os.environ.get(
        "DEEPSEEK_SYSTEM_PROMPT",
        "你是一个智能对话助手，请用简洁清晰的中文回答问题。"
    )
    TIMEOUT = 30       # 请求超时秒数
    MAX_RETRIES = 2    # 最大重试次数

    @classmethod
    def _build_messages(cls, context: list) -> list:
        """
        构建完整的 messages 数组（System Prompt + 上下文）

        Args:
            context: 已有的消息上下文（含 system 可能）

        Returns:
            格式化后的 messages 列表
        """
        messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]

        # 如果 context 第一项已经是 system，则替换
        if context and context[0].get("role") == "system":
            context = context[1:]

        messages.extend(context)
        return messages

    @classmethod
    def chat_stream(cls, context: list, on_token, on_done=None, on_error=None):
        """
        流式对话（SSE 逐 Token 推送）

        Args:
            context:     消息上下文（不含 system prompt）
            on_token:    Token 回调函数（每收到一个 token 调用一次）
            on_done:     完成回调（传入完整回复文本）
            on_error:    错误回调（传入错误消息字符串）

        流式处理说明：
        - stream=True 启用 SSE 流式返回
        - iter_lines() 逐行解析 SSE 事件
        - 每行格式: data: {"choices":[{"delta":{"content":"你好"}}]}
        - "[DONE]" 表示流结束
        """
        messages = cls._build_messages(context)
        full_reply = []

        for attempt in range(cls.MAX_RETRIES + 1):
            try:
                response = requests.post(
                    f"{cls.BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {cls.API_KEY}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                    json={
                        "model": cls.MODEL,
                        "messages": messages,
                        "stream": True,
                        "temperature": 0.7,
                        "max_tokens": 4096,
                    },
                    stream=True,
                    timeout=cls.TIMEOUT,
                )

                if not response.ok:
                    error_msg = f"API 请求失败 ({response.status_code})"
                    if on_error:
                        on_error(error_msg)
                    return

                # 逐行解析 SSE 流
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]  # 去掉 "data: " 前缀
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_reply.append(content)
                                    on_token(content)
                        except json.JSONDecodeError:
                            continue

                break  # 成功，退出重试循环

            except requests.exceptions.Timeout:
                if attempt < cls.MAX_RETRIES:
                    time.sleep(1)  # 重试前等待1秒
                    continue
                if on_error:
                    on_error("请求超时，请稍后重试")
            except requests.exceptions.ConnectionError:
                if attempt < cls.MAX_RETRIES:
                    time.sleep(1)
                    continue
                if on_error:
                    on_error("网络连接失败，请检查网络")
            except Exception:
                traceback.print_exc()
                if attempt < cls.MAX_RETRIES:
                    time.sleep(1)
                    continue
                if on_error:
                    on_error("AI 服务异常，请稍后重试")

        # 流结束回调
        if on_done:
            on_done("".join(full_reply))

    @classmethod
    def _build_messages_with_tools(cls, context: list) -> list:
        """构建含 tool_calls 的完整 messages"""
        from owl_ai.util.tool_executor import TOOLS_SCHEMA
        system_prompt = (
            "你是一个博客管理助手，可以通过工具帮助用户管理文章。"
            "当用户请求查询文章列表或创建文章时，请调用相应工具。"
            "如果工具返回了结果，请基于结果生成自然语言回复。"
            "生成文章草稿时，请使用自然段落描述，避免大量#号一级标题，"
            "正文使用普通段落+小标题（如**加粗**）即可，适配后台富文本编辑器。"
        )
        messages = [{"role": "system", "content": system_prompt}]
        if context and context[0].get("role") == "system":
            messages[0] = context[0]
            context = context[1:]
        messages.extend(context)
        return messages, TOOLS_SCHEMA

    @classmethod
    def chat_sync_with_tools(cls, context: list, user_id: int) -> dict:
        """
        Function Calling 工具调用模式

        Returns:
            dict: {"reply": str, "tool_used": bool, "usage": dict or None}
        """
        from owl_ai.util.tool_executor import ToolExecutor

        messages, tools = cls._build_messages_with_tools(context)
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        def _sanitize(content):
            """过滤DSML/tool_calls等原生标记，只保留自然语言"""
            import re
            content = re.sub(r'<\s*\|?\s*DSML\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\s*\|?\s*tool_calls\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\s*\|?\s*invoke\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<\s*\|?\s*function_call\s*\|?\s*>', '', content, flags=re.IGNORECASE)
            return content.strip()

        try:
            response = requests.post(
                f"{cls.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {cls.API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": cls.MODEL,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.7,
                    "max_tokens": 2048
                },
                timeout=cls.TIMEOUT
            )
            if not response.ok:
                return {"reply": None, "tool_used": False, "usage": total_usage}

            data = response.json()
            usage1 = data.get("usage", {})
            total_usage["prompt_tokens"] += usage1.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage1.get("completion_tokens", 0)
            total_usage["total_tokens"] += usage1.get("total_tokens", 0)

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            tool_calls = message.get("tool_calls", [])
            if not tool_calls:
                return {"reply": _sanitize(message.get("content", "")), "tool_used": False, "usage": total_usage}

            tool_results = []
            for tc in tool_calls:
                func_info = tc.get("function", {})
                tool_name = func_info.get("name", "")
                try:
                    args = json.loads(func_info.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                result = ToolExecutor.execute(user_id, tool_name, args)
                tool_results.append({
                    "tool_call_id": tc.get("id", ""),
                    "name": tool_name,
                    "result": result
                })

            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": tr["result"]
                })

            response2 = requests.post(
                f"{cls.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {cls.API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": cls.MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                timeout=cls.TIMEOUT
            )
            if response2.ok:
                data2 = response2.json()
                usage2 = data2.get("usage", {})
                total_usage["prompt_tokens"] += usage2.get("prompt_tokens", 0)
                total_usage["completion_tokens"] += usage2.get("completion_tokens", 0)
                total_usage["total_tokens"] += usage2.get("total_tokens", 0)
                content = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"reply": _sanitize(content) or "操作已完成", "tool_used": True, "usage": total_usage}

            return {"reply": "生成内容耗时较长，请重新提问", "tool_used": True, "usage": total_usage}

        except requests.exceptions.Timeout:
            return {"reply": "生成内容耗时较长，请重新提问", "tool_used": True, "usage": total_usage}
        except Exception:
            return {"reply": None, "tool_used": False, "usage": total_usage}

