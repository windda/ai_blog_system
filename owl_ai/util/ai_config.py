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
import base64
import hashlib

DEFAULT_MODEL = 'deepseek-chat'
SUPPORTED_MODELS = ['deepseek-chat', 'deepseek-reasoner', 'deepseek-flash', 'deepseek-v4-flash', 'deepseek-coder']

# 加密密钥（对称加密，生产环境建议从环境变量 ENC_SECRET 读取）
_ENCRYPT_SECRET = os.environ.get('AI_KEY_ENC_SECRET', 'ai-blog-system-local-secret-2026')


def _derive_key() -> bytes:
    """从密钥派生 32 字节加密 key"""
    return hashlib.sha256(_ENCRYPT_SECRET.encode('utf-8')).digest()


def _encrypt(plaintext: str) -> str:
    """对称加密（XOR + SHA256 派生 key + base64），禁止明文入库"""
    if not plaintext:
        return ''
    key = _derive_key()
    data = plaintext.encode('utf-8')
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode('ascii')


def _decrypt(ciphertext: str) -> str:
    """解密"""
    if not ciphertext:
        return ''
    try:
        key = _derive_key()
        data = base64.urlsafe_b64decode(ciphertext.encode('ascii'))
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return decrypted.decode('utf-8')
    except Exception:
        return ''


def encrypt_text(plaintext: str) -> str:
    """加密文本（供平台全局 Key 等场景复用）"""
    return _encrypt(plaintext)


def decrypt_text(ciphertext: str) -> str:
    """解密文本"""
    return _decrypt(ciphertext)


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
    """读取指定用户的 API Key（加密存储，读取时解密）"""
    stored = (_user_cfg(user_id).get('deepseek_api_key') or '').strip()
    if not stored:
        return ''
    # 兼容旧数据：明文 sk- 开头直接返回；否则是密文，解密
    if stored.startswith('sk-'):
        return stored
    return _decrypt(stored).strip()


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
        user_cfg['deepseek_api_key'] = _encrypt(api_key.strip())  # 加密存储，禁止明文入库
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
    """校验 API Key 格式合法性（不限制 sk- 前缀，兼容各模型厂商 Key 格式）

    只做基础合法性判断：非空 + 不含空白字符。
    """
    key = (key or '').strip()
    return bool(key) and not any(c.isspace() for c in key)
