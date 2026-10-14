# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置（onefile 单文件 exe）。

打包命令：pyinstaller app.spec
"""

import os
import sys

# 确保 collect_submodules 能在项目根目录找到 owl_* 包
sys.path.insert(0, os.path.abspath('.'))

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# 收集所有 owl_ 模块（框架用 import_module 动态导入，静态分析发现不了）
# 用文件系统遍历生成完整模块列表：collect_submodules 依赖 import 递归，
# 而 owl 子包 import 时会因依赖运行时状态（reg/token.header）失败，导致收集不完整
hiddenimports = []
for _md in ['owl_admin', 'owl_blog', 'owl_system', 'owl_framework',
            'owl_common', 'owl_ai', 'owl_apscheduler']:
    for _root, _dirs, _files in os.walk(_md):
        for _f in _files:
            if _f.endswith('.py'):
                _rel = os.path.join(_root, _f)
                _mn = _rel[:-3].replace(os.sep, '.').replace('/', '.')
                if _mn.endswith('.__init__'):
                    _mn = _mn[:-9]
                hiddenimports.append(_mn)

# 数据文件
datas = [
    ('owl-ui/dist', 'owl-ui/dist'),           # 前端静态资源
    ('owl_admin/instance/app.db', '.'),  # 种子数据库（解压后 _MEIPASS/app.db）
    ('owl_admin/config', 'owl_admin/config'), # YAML 配置文件
    ('owl_admin/uploads', 'uploads'),         # 上传的图片（文章封面/头像）
]
# captcha 验证码字体/音频
datas += collect_data_files('captcha')

a = Analysis(
    ['run.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI_Blog_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
