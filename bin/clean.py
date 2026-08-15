import os
import shutil
from pathlib import Path

PROJECT_ROOT =  os.path.join(os.path.abspath(__file__),os.pardir,os.pardir)

def clean_python_cache():
    """
    清理Python缓存文件和目录
    - __pycache__ 目录
    - .pyc 文件
    - .pyo 文件
    - .pyd 文件
    """
    # 转换为Path对象
    base_path = Path(PROJECT_ROOT)
    
    # 要清理的文件类型
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        # "**/*.pyo",
        # "**/*.pyd"
    ]
    
    total_removed = 0
    
    for pattern in cache_patterns:
        for path in base_path.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
                else:
                    path.unlink()
                    print(f"Removed file: {path}")
                total_removed += 1
            except Exception as e:
                print(f"Error removing {path}: {e}")
    
    print(f"\nTotal items removed: {total_removed}")

if __name__ == "__main__":
    clean_python_cache()
