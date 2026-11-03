# MySwap Local

在本地运行的 MySwap (taiji implant/种殖) - 一个纯文本分享工具。

## 快速开始

```bash
# 1. 进入项目目录
cd myswap

# 2. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# 3. 运行应用
python -m flask --app run:app run --host 127.0.0.1 --port 5000 --no-debugger --no-reload

# 4. 在浏览器中访问
# http://127.0.0.1:5000
```

## 功能特性

- **无登录设计**：使用密码验证，无 session/cookie
- **Swap**：纯文本内容单元，支持自定义别名 (alias)
- **Stacueue**：Stack + Queue 的融合理念
- **D_C_date**：从生日计算的特殊日期计数
- **Friends**：朋友列表，显示在用户主页
- **UserAliases**：要显示的 Swap 别名列表
- **Strip 模式**：纯文本输出模式
- **Scraper**：网页标题抓取

## URL 路由

| 路径 | 说明 |
|------|------|
| `/` | 首页 |
| `/Signup` | 注册 |
| `/<username>` | 用户主页 |
| `/<username>/<alias>` | 单个 Swap 页面 |
| `/<username>/setting` | 设置页面 |
| `/<username>/auth` | 验证页面 |
| `/<username>/RANDOM` | 黑色背景特殊页面 |
| `/<username>/WDDC` | 带时间的黑色背景页面 |
| `/myswap/faq` | 常见问题 |
| `/myswap/myswap-about` | 关于 |

## 密码与本地运行

不提供通用管理密码。新密码使用 Werkzeug 的带盐密码哈希；现有 SHA1 账户在本人密码验证成功后自动升级。

默认仅监听本机回环地址。此版本用于本地试用，尚未完成面向公网的完整安全审查，不应直接公开部署。

## 回归测试

```bash
python -m unittest discover -s tests -v
```

## 数据存储

使用 SQLite 数据库存储在 `myswap.db` 文件中。

## 技术栈

- Python 3
- Flask
- SQLite
- Blueprint CSS
- jQuery
