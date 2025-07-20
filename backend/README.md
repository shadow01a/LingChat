 # LingChat

## 项目介绍

LingChat是一个基于AI的智能聊天系统，具有情感分析、语音合成、桌面宠物等多种功能。

### 主要特性

- 🤖 **智能对话**: 基于DeepSeek API的自然语言处理
- 😊 **情感分析**: 18种情感状态识别和可视化表达
- 🔊 **语音合成**: 支持VITS模型的高质量语音输出
- 🐾 **桌面宠物**: 可爱的桌面AI助手
- 💾 **记忆系统**: RAG技术实现的长期记忆功能
- 🌐 **Web界面**: 现代化的前端用户界面
- 🔗 **WebSocket**: 实时双向通信

### 技术栈

- **后端**: Python, FastAPI, WebSocket
- **前端**: HTML, CSS, JavaScript
- **AI模型**: DeepSeek
- **语音**: VITS TTS
- **数据库**: SQLite
- **部署**: Docker (可选)

## Relese安装

### 下载&使用exe程序

- 在[Release](https://github.com/SlimeBoyOwO/LingChat/releases)中下载附件，并解压。
- 解压后，使用记事本打开app文件夹.env，在.env中填入你的apikey。deepseek apikey登录[DeepSeek 开放平台](https://platform.deepseek.com/usage)后获取。请妥善保管自己的apikey。
- 点击LingChat.exe启动程序
- (非必须):若要使用语音功能，请下载[simple-vits-api](https://github.com/Artrajz/vits-simple-api)链接程序。该项目实现了基于 VITS 的简单语音合成 API。建议下载GPU版本，速度快。程序默认监听23456语音端口，程序默认导入的模型是zcchat地址->讨论区->角色示范（丛雨）->vits模型下载好之后在simple-vits-api的目录的/data/models里面解压，再启动就ok了;如果需要使用其他模型，在.env的Vits实现函数更改相关设定即可。
- app文件夹内的rag_chat_history文件夹的所有对话记忆将被永久储存。打开RAG开关后，本轮对话将会储存在rag_chat_history文件夹内。**如果你手动更改了该文件夹内部的对话记录，请手动删除app文件夹下的整个chroma_db_store文件夹以更新记忆库**。该文件夹是提高启动速度的永久记忆缓存区域。

### 下载情感分类模型

情感分类模型已包含在Releases中，双击exe即可启动。源代码内不包含，请手动下载release然后移动过去。

## 源码部署

### Linux

+ 环境配置
  
  ```bash
  conda create -n LingChat python=3.12
  conda activate LingChat
  pip install -r requirement.txt
  ```

+ API KEY配置
  
  ```bash
  cp ./.env.example ./.env
  ```
  
  然后将.env中的CHAT_API_KEY和VD_API_KEY替换为自己的API key。

+ 情绪推理模型和声音下载
  
  （兄弟们先将就着从relese包里面解压出来吧。）
  
  ```bash
  cp <relese-file-path>/app/backend/emotion_model_18emo/model.safetensors <source-code-path>/backend/emotion_model_18emo/
  cp <relese-file-path>/app/frontend/public/audio/* <source-code-path>/frontend/public/audio/
  ```

+ 运行
  
  ```bash
  python ./backend/windows_main.py
  ```
  
  PS：你没看错，Linux的启动文件也是windows_main.py ........

### Windows

+ 环境配置
  
  **方法一：使用Conda（推荐）**
  
  ```cmd
  conda create -n LingChat python=3.12
  conda activate LingChat
  pip install -r requirements.txt
  ```
  
  **方法二：使用Python虚拟环境**
  
  ```cmd
  python -m venv LingChat
  LingChat\Scripts\activate
  pip install -r requirements.txt
  ```

+ API KEY配置
  
  ```cmd
  copy .env.example .env
  ```
  
  然后使用记事本或其他文本编辑器打开`.env`文件，将其中的`CHAT_API_KEY`和`VD_API_KEY`替换为自己的API key。
  
  或者在命令行中直接编辑：
  
  ```cmd
  notepad .env
  ```

+ 情绪推理模型和声音下载
  
  （同Linux，可从release包里面解压）

+ 运行
  
  **方法一：使用Python直接运行**
  
  ```cmd
  python .\backend\windows_main.py
  ```
  
  **方法二：使用批处理文件**
  
  双击根目录下的`start.windows.bat`文件启动程序。
  
  **方法三：使用桌面宠物模式**
  
  双击根目录下的`desk_pet.bat`文件启动桌面宠物版本。

## 开发文档

### 项目结构

```
LingChat/
├── backend/                    # 后端代码
│   ├── api/                   # API路由和处理
│   ├── core/                  # 核心功能模块
│   ├── database/              # 数据库相关
│   ├── desktop_pet/           # 桌面宠物功能
│   ├── emotion_model_*/       # 情感分析模型
│   ├── go-impl/              # Go语言实现
│   └── utils/                # 工具函数
├── frontend/                  # 前端代码
├── characters/               # 角色图片资源
├── data/                     # 数据文件
└── logs/                     # 日志文件
```

### 核心模块说明

+ **ai_service.py**: AI服务核心，处理与AI模型的交互
+ **deepseek.py**: DeepSeek API集成
+ **predictor.py**: 情感预测功能
+ **VitsTTS.py**: 语音合成功能
+ **websocket_server.py**: WebSocket服务器
+ **RAG.py**: 检索增强生成功能

### API接口文档

#### 聊天接口（pending）

- **POST** `/api/chat`
  - 功能：发送聊天消息
  - 参数：`message`, `user_id`, `session_id`

#### 情感分析接口（pending）

- **POST** `/api/emotion`
  - 功能：分析文本情感
  - 参数：`text`

#### 语音合成接口（pending）

- **POST** `/api/tts`
  - 功能：文本转语音
  - 参数：`text`, `voice_model`

### 开发指南

    pending

# 

### 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 许可证

查看LICENSE文件了解详细信息。