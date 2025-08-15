# 🐈✨ LingChat - Develop(开发版)

![official](https://github.com/user-attachments/assets/ffccbe79-87ed-4dbc-8e60-f400efbbab26)

## 安装

### 通过 pip 安装

您可能希望在虚拟环境中安装软件包以避免与其他软件包发生冲突。您可以使用 `venv` 创建虚拟环境。

```bash
python -m venv .venv
```

然后激活虚拟环境：

```bash
source .venv/bin/activate  # 在 Linux 或 macOS 上
.venv\Scripts\activate  # 在 Windows 上
```

使用 pip 安装LingChat：

```bash
pip install .
```

### 通过 poetry 安装

您可以使用 poetry 安装软件包：

```bash
poetry install
```

## 使用方法

### 添加您的密钥

在项目的根目录中创建一个名为 `.env` 的文件，并将的API 密钥添加到其中：

```text
CHAT_API_KEY="api key的位置"
```

### 运行服务器

运行以下命令启动服务器：

```bash
# 如果您通过 pip 安装了软件包
# python -m ling_chat
# 或者:
poetry run python -m ling_chat
```

## 项目结构

```txt
ling_chat
├── ling_chat          # 主包目录
│   ├── __init__.py
│   ├── api            # API 相关代码
│   ├── core           # 核心功能
│   ├── database       # 数据库相关代码
│   ├── static
│   │   ├── frontend   # 前端文件
│   │   └── game_data  # 游戏数据文件
│   ├── third_party    # 第三方集成
│   │   ├── emotion_model_18emo  # 18种情绪的情感模型
│   │   └── vits-simple-api      # 用于文本转语音的 VITS Simple API
│   ├── utils           # 工具函数
│   ├── __init__.py
│   ├── __main__.py
│   └── main.py         # 主入口点
├── data                # 用户数据文件
├── docs                # 文档文件（最新文档已迁移，此为旧版存档）
├── tests               # 测试文件
├── .env                # 环境变量文件 (用户应自己创建此文件)
├── .env.example        # 环境变量示例文件
├── .gitignore          # Git 忽略文件
├── README.md           # 项目 README 文件
└── pyproject.toml      # Poetry 配置文件
```

# 更新计划

## 服务端支持

by [Vickko](https://github.com/Vickko)

基于LingChat 0.3已实现的功能，使用go搭建服务端代码，并提供登录即用的服务。

详见[go-impl分支](https://github.com/SlimeBoyOwO/LingChat/tree/feat/go-impl)

## 游戏引擎重构

by [风雪](https://github.com/T-Auto)

增加长线预设剧情支持，兼容肉鸽旅行/COC/DND/狼人杀等剧本呈现方式，且原生兼容读档存档、多人物同屏和记忆库系统的底层框架。

详见Issues：[【0.4.0开发日志】长剧情系统＆多角色同屏＆随机事件演进＆小游戏框架](https://github.com/SlimeBoyOwO/LingChat/issues/91)，源码位于仓库[NeoChat](https://github.com/T-Auto/NeoChat)，剧情方面参考[NeoChat剧情创作指南](https://github.com/T-Auto/NeoChat/blob/main/NeoChat%20%E5%89%A7%E6%83%85%E5%88%9B%E4%BD%9C%E6%8C%87%E5%8D%97.md)

## 记忆系统重构

by [云](https://github.com/LtePrince)

重构记忆系统，使用图数据库实现RAG来提升性能。

详见Issues：[【0.4.0开发日志】基于图数据库实现RAG](https://github.com/SlimeBoyOwO/LingChat/issues/82)，源码位于仓库[LongTermMemoryRAG](https://github.com/LtePrince/LongTermMemoryRAG)

## 新的UI

by [yukito](https://github.com/yukito0209)、[喵](https://github.com/a2942)

更好看的启动UI！

详见Demo：[main_page_demo](https://github.com/SlimeBoyOwO/LingChat/tree/develop/Demo/main_page_demo)

## 模块化的api兼容层

by [uwa](https://github.com/myh1011)

将任意api转为标准openai格式，实现对各种api的系统性支持。

详见Demo：[EPU-Api](https://github.com/SlimeBoyOwO/LingChat/tree/develop/Demo/epu-api)

或github [EPU-Api](https://github.com/myh1011/epu_api)

## 桌宠启动方式

by [dada](https://github.com/kono-dada)

提供轻量化的桌宠启动方式。

现已迁移至：[Ling-Pet项目](https://github.com/kono-dada/Ling-Pet)

## 多语言框架

by [Thz922](https://github.com/Thz922)

为LingChat添加多语言支持。

详见Issues：[为项目添加多语言支持 · Issue #129 · SlimeBoyOwO/LingChat](https://github.com/SlimeBoyOwO/LingChat/issues/129)

## 安卓端开发

by [shadow01a](https://github.com/shadow01a)

探索安卓端的使用。

目前已经有了[可用的文档](https://lingchat.wiki/manual/deployment/android_deploy.html)

## 文档

by [foxcyber907](https://github.com/foxcyber907)

拆分文档部分并独立更新。

详见网站 [LingChat Wiki](https://lingchat.wiki/) 或者 [GitHub 仓库](https://github.com/foxcyber907/ling-docs)

## 前端重构

使用vue彻底重构前端。

详见[frontend_vue](https://github.com/SlimeBoyOwO/LingChat/tree/develop/frontend_vue)