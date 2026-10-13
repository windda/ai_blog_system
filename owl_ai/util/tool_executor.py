# -*- coding: utf-8 -*-
"""
Function Calling 工具执行器。

将大模型返回的 tool_calls 结构化参数转换为本地业务调用，
并对工具执行结果进行格式化，回传给 LLM 生成自然语言回复。
"""

import json
from datetime import datetime

from owl_admin.ext import db


# DeepSeek 兼容的 OpenAI Function Calling 工具 Schema
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_user_articles",
            "description": "查询当前登录用户的所有文章列表。无需任何参数，自动识别当前用户并返回其全部文章。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_article_draft",
            "description": "为用户创建一篇博客文章草稿并保存到数据库。标题和正文由大模型自动生成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "文章标题"
                    },
                    "content": {
                        "type": "string",
                        "description": "文章正文内容，支持 Markdown 格式"
                    }
                },
                "required": ["title", "content"]
            }
        }
    }
]


TOOLS_MAP = {
    "get_user_articles": "查询用户文章",
    "create_article_draft": "创建文章草稿"
}


class ToolExecutor:
    """工具执行器 — 将 LLM tool_calls 转为本地业务操作"""

    @staticmethod
    def execute(user_id: int, tool_name: str, arguments: dict) -> str:
        """
        执行工具调用并返回格式化结果文本

        Args:
            user_id: 当前登录用户ID
            tool_name: 工具名称
            arguments: 工具参数（已解析的 dict）
        """
        if tool_name == "get_user_articles":
            return ToolExecutor._get_user_articles(user_id)
        elif tool_name == "create_article_draft":
            return ToolExecutor._create_article_draft(user_id, arguments)
        else:
            return f"未知工具：{tool_name}"

    @staticmethod
    def _get_user_articles(user_id: int) -> str:
        """查询用户文章"""
        try:
            from owl_blog.service import BlogArticleService
            from owl_blog.domain.entity import BlogArticle
            dto = BlogArticle()
            dto.author_id = user_id
            articles = BlogArticleService.select_article_list(dto)
            if not articles:
                return "您目前还没有发布任何文章。"

            lines = [f"您共有 {len(articles)} 篇文章："]
            for a in articles:
                title = getattr(a, 'title', '无标题')
                status = getattr(a, 'status', '0')
                status_text = "已发布" if status == '1' else "草稿"
                create_time = str(getattr(a, 'create_time', ''))[:10]
                lines.append(f"- [{status_text}] {title} (创建于 {create_time})")
            return "\n".join(lines)
        except Exception as e:
            return f"查询文章时出现错误：{str(e)}，请稍后重试。"

    @staticmethod
    def _create_article_draft(user_id: int, arguments: dict) -> str:
        """创建文章草稿"""
        try:
            title = (arguments.get("title", "") or "").strip()
            content = (arguments.get("content", "") or "").strip()
            if not title:
                return "创建草稿失败：文章标题不能为空。"
            if not content:
                return "创建草稿失败：文章内容不能为空。"

            from owl_blog.service import BlogArticleService
            from owl_blog.domain.entity import BlogArticle
            from owl_blog.utils import sanitize_html

            dto = BlogArticle(
                title=title,
                content=sanitize_html(content),
                author_id=user_id,
                status='0',  # 草稿状态
            )
            dto.create_by_user(str(user_id))
            BlogArticleService.insert_article(dto)
            return f"文章草稿《{title}》已成功创建并保存到您的后台。您可以在「我的文章」中查看和编辑。"
        except Exception as e:
            return f"创建文章草稿时出现错误：{str(e)}，请稍后重试。"