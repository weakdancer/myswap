#!/usr/bin/env python3
import sys
import os

# 添加 app 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("MySwap - Stacueue (Stack + Queue)")
    print("本地地址: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
