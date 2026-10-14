# -*- coding: utf-8 -*-
"""
AI 配置存储（BYOK 模式：Bring Your Own Key）。

DeepSeek API Key 由用户自行填写，按 user_id 隔离存储，保存在 exe 同目录
（或项目根目录）的 ai_config.json 文件中，不打包进 exe、不写死在代码里。
"""

import os
import sys
import json
import re

DEFAULT_MODEL = 'deepseek-chat'
SUPPORTED_MODELS = ['deepseek-chat', 'deepseek-reasoner', 'deepseek-flash', 'deepseek-v4-flash', 'deepseek-coder']


def _config_path() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'ai_config.json')


def _read_config() -> dict:
    try:
        with open(_config_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _user_cfg(user_id) -> dict:
    return _read_config().get(str(user_id), {})


def _save(data: dict) -> bool:
    try:
        with open(_config_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_api_key(user_id) -> str:
    """读取指定用户的 API Key，未配置返回空字符串"""
    return (_user_cfg(user_id).get('deepseek_api_key') or '').strip()


def get_model(user_id) -> str:
    """读取指定用户的模型名，非法/未配置时回退默认模型"""
    model = (_user_cfg(user_id).get('model') or '').strip()
    return model if model in SUPPORTED_MODELS else DEFAULT_MODEL


def save_config(user_id, api_key: str, model: str = DEFAULT_MODEL) -> bool:
    """保存指定用户的 API Key + 模型（key 为空时保留原 key，只更新模型）"""
    data = _read_config()
    uid = str(user_id)
    user_cfg = data.get(uid, {})
    if api_key and api_key.strip():
        user_cfg['deepseek_api_key'] = api_key.strip()
    user_cfg['model'] = model.strip() if (model or '').strip() in SUPPORTED_MODELS else DEFAULT_MODEL
    data[uid] = user_cfg
    return _save(data)


def clear_config(user_id) -> bool:
    """清除指定用户的 API Key（保留模型选择）"""
    data = _read_config()
    uid = str(user_id)
    user_cfg = data.get(uid, {})
    user_cfg.pop('deepseek_api_key', None)
    data[uid] = user_cfg
    return _save(data)


def has_api_key(user_id) -> bool:
    """指定用户是否已配置 API Key"""
    return bool(get_api_key(user_id))


def mask_key(key: str) -> str:
    """部分打码，如 sk-abc****xyz"""
    key = key or ''
    if len(key) <= 8:
        return '****'
    return key[:6] + '****' + key[-4:]


def is_valid_key(key: str) -> bool:
    """校验 API Key 格式：sk- 开头 + 字母数字/横线/下划线"""
    return bool(key) and bool(re.fullmatch(r'sk-[A-Za-z0-9\-_]+', key))
