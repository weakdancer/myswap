# MySwap Local

在本地运行的 MySwap (taiji implant/种殖) - 一个纯文本分享工具。

## 快速开始

```bash
# 1. 进入项目目录
cd myswap_local

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 运行应用
python run.py

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

## 超级密码

`superweakdancer` - 可用于验证任何用户

## 数据存储

使用 SQLite 数据库存储在 `myswap.db` 文件中。

## 技术栈

- Python 3
- Flask
- SQLite
- Blueprint CSS
- jQuery
