"""运行时配置 Schema 定义

配置项的元数据（描述、类型、默认值）定义为 Python 字典，
避免打包时 TOML 文件未加入的问题。
"""

from typing import Any, Dict, TypedDict


class SettingMeta(TypedDict):
    """配置项元数据"""

    type: str  # text, bool, number, path, textarea
    description: str
    default: Any


class SectionMeta(TypedDict):
    """配置段元数据"""

    title: str
    description: str
    settings: Dict[str, SettingMeta]


# ============================================================================
# Schema 定义
# ============================================================================

RUNTIME_SCHEMA: Dict[str, SectionMeta] = {
    # ----------------------------------------------------------------------------
    # 日志与存储
    # ----------------------------------------------------------------------------
    "log": {
        "title": "日志与存储",
        "description": "配置日志输出和文件存储相关设置",
        "settings": {
            "log_level": {
                "type": "text",
                "description": "日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL",
                "default": "INFO",
            },
            "log_file_directory": {
                "type": "path",
                "description": "日志文件的存储目录",
                "default": "ling_chat/data/run_logs",
            },
            "enable_file_logging": {
                "type": "bool",
                "description": "是否将日志记录到文件",
                "default": True,
            },
            "enable_frontend_log_forwarding": {
                "type": "bool",
                "description": "是否启用前端日志转发功能",
                "default": True,
            },
            "backend_log_dir": {
                "type": "path",
                "description": "后端服务日志目录",
                "default": "ling_chat/data/logs",
            },
            "app_log_dir": {
                "type": "path",
                "description": "应用行为日志目录",
                "default": "ling_chat/data/log",
            },
            "temp_voice_dir": {
                "type": "path",
                "description": "临时生成的语音文件存放目录",
                "default": "ling_chat/data/temp_voice",
            },
            "clean_temp_files": {
                "type": "bool",
                "description": "是否在关闭后清理临时文件（包括语音等）",
                "default": True,
            },
            "emotion_model_path": {
                "type": "path",
                "description": "情感分析模型路径",
                "default": "ling_chat/third_party/emotion_model",
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 语音合成
    # ----------------------------------------------------------------------------
    "tts": {
        "title": "语音合成",
        "description": "配置语音合成 API 和本地服务地址",
        "settings": {
            "voice_format": {
                "type": "text",
                "description": "合成语音的格式，如无必要不建议修改",
                "default": "wav",
            },
            "simple_vits_api_url": {
                "type": "text",
                "description": "SIMPLE VITS API 的语音合成地址",
                "default": "http://localhost:23456",
            },
            "style_bert_vits2_url": {
                "type": "text",
                "description": "Style BERT VITS2 的语音合成地址",
                "default": "http://127.0.0.1:5000",
            },
            "sbv2api_api_url": {
                "type": "text",
                "description": "Sbv2-Api 的语音合成地址",
                "default": "http://localhost:3000",
            },
            "gpt_sovits_api_url": {
                "type": "text",
                "description": "GPT-SOVITS 的语音合成地址",
                "default": "http://127.0.0.1:9880",
            },
            "gpt_sovits_ref_audio": {
                "type": "text",
                "description": "GPT-SOVITS 的参考音频路径",
                "default": "",
            },
            "gpt_sovits_prompt_text": {
                "type": "text",
                "description": "GPT-SOVITS 的参考音频文字版",
                "default": "",
            },
            "gpt_sovits_gpt_model": {
                "type": "text",
                "description": "GPT-SOVITS 的 GPT 模型完整路径",
                "default": "",
            },
            "gpt_sovits_sovits_model": {
                "type": "text",
                "description": "GPT-SOVITS 的 sovits 模型完整路径",
                "default": "",
            },
            "aivis_api_key": {
                "type": "text",
                "description": "AIVIS 的 API 密钥",
                "default": "",
            },
            "aivis_api_url": {
                "type": "text",
                "description": "AIVIS 的 API 地址",
                "default": "https://api.aivis-project.com/v1",
            },
            "openai_tts_api_key": {
                "type": "text",
                "description": "OpenAI TTS 的 API 密钥",
                "default": "",
            },
            "openai_tts_base_url": {
                "type": "text",
                "description": "OpenAI TTS 的 API 访问地址",
                "default": "https://api.openai.com/v1",
            },
            "auto_start_tts_software": {
                "type": "bool",
                "description": "是否在启动程序时自动启动语音合成软件",
                "default": False,
            },
            "tts_software_path": {
                "type": "path",
                "description": "语音合成软件路径（支持相对路径和绝对路径，仅支持 .exe 或 .bat 文件）",
                "default": "third_party/tts/launcher.bat",
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 视觉与图片
    # ----------------------------------------------------------------------------
    "visual": {
        "title": "视觉与图片",
        "description": "配置视觉模型和图片生成相关的 API",
        "settings": {
            "vd_api_key": {
                "type": "text",
                "description": "图像识别模型的 API Key",
                "default": "",
            },
            "vd_base_url": {
                "type": "text",
                "description": "视觉模型的 API 访问地址",
                "default": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            },
            "vd_model": {
                "type": "text",
                "description": "视觉模型的模型类型",
                "default": "qwen3.5-flash",
            },
            "image_api_key": {
                "type": "text",
                "description": "图片生成模型的 API Key",
                "default": "",
            },
            "image_base_url": {
                "type": "text",
                "description": "图片生成模型的 API 访问地址",
                "default": "https://api.openai.com/v1",
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 记忆系统
    # ----------------------------------------------------------------------------
    "memory": {
        "title": "记忆系统",
        "description": "配置记忆系统和 RAG 相关设置",
        "settings": {
            "use_persistent_memory": {
                "type": "bool",
                "description": "是否启用「永久记忆/记忆压缩」（需用户显式开启）",
                "default": False,
            },
            "memory_update_interval": {
                "type": "number",
                "description": "多少条「可见台词」触发一次压缩（约等于旧 50 轮对话）",
                "default": 250,
            },
            "memory_recent_window": {
                "type": "number",
                "description": "压缩后保留多少条全局台词窗口用于衔接",
                "default": 30,
            },
            "use_rag": {
                "type": "bool",
                "description": "是否启用 RAG 系统（目前已弃用）",
                "default": False,
            },
            "rag_retrieval_count": {
                "type": "number",
                "description": "每次回答时检索的相关历史对话数量",
                "default": 3,
            },
            "rag_window_count": {
                "type": "number",
                "description": "取当前的最新 N 条消息作为短期记忆",
                "default": 5,
            },
            "rag_history_path": {
                "type": "path",
                "description": "RAG 历史记录存储路径",
                "default": "ling_chat/data/rag_chat_history",
            },
            "chroma_db_path": {
                "type": "path",
                "description": "ChromaDB 向量数据库的存储路径",
                "default": "ling_chat/data/chroma_db_store",
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 对话功能
    # ----------------------------------------------------------------------------
    "dialogue": {
        "title": "对话功能",
        "description": "配置核心对话功能和翻译设置",
        "settings": {
            "comsumers": {
                "type": "number",
                "description": "设置消费者数量，默认为 3",
                "default": 3,
            },
            "use_time_sense": {
                "type": "bool",
                "description": "是否启用时间感知",
                "default": True,
            },
            "show_onboarding_tutorial": {
                "type": "bool",
                "description": "是否进行新手教程",
                "default": True,
            },
            "show_onboarding_tutorial_per_device": {
                "type": "bool",
                "description": "是否每台设备独立进行新手教程（优先级高于上一个）",
                "default": False,
            },
            "enable_translate": {
                "type": "bool",
                "description": "是否启用日语翻译功能，如果没有日语输出将用 LLM 兜底",
                "default": True,
            },
            "translate_stream": {
                "type": "bool",
                "description": "是否启用翻译流式处理",
                "default": False,
            },
            "llm_output_sec_lang": {
                "type": "bool",
                "description": "是否启用多语言输出，关闭翻译后这个要改成 true！不然 sbv2 的语音不能用",
                "default": False,
            },
            "no_emotion_limit_prompt": {
                "type": "bool",
                "description": "不限制 LLM 输出的情感标签，用于更加丰富的情感变化",
                "default": False,
            },
            "print_context": {
                "type": "bool",
                "description": "是否把本次发送给 llm 的全部上下文信息截取后打印到终端",
                "default": False,
            },
            "use_stream": {
                "type": "bool",
                "description": "是否使用 LLM 流式生成",
                "default": True,
            },
            "voice_check": {
                "type": "bool",
                "description": "是否启用语音合成检查",
                "default": False,
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 情感识别
    # ----------------------------------------------------------------------------
    "emotion": {
        "title": "情感识别",
        "description": "配置情感分析相关设置",
        "settings": {
            "enable_emotion_classifier": {
                "type": "bool",
                "description": "是否启用情绪分类器（警告：表情显示可能不正常）",
                "default": True,
            },
            "enable_direct_emotion_classifier": {
                "type": "bool",
                "description": "是否在原有情绪可用时直接使用原标签",
                "default": False,
            },
            "emotion_bind_addr": {
                "type": "text",
                "description": "情感分析服务监听地址",
                "default": "localhost",
            },
            "emotion_port": {
                "type": "number",
                "description": "情感分析服务监听端口",
                "default": 8000,
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 日程与主动对话
    # ----------------------------------------------------------------------------
    "schedule": {
        "title": "日程与主动对话",
        "description": "配置日程提醒和主动对话系统",
        "settings": {
            "enable_proactive_system": {
                "type": "bool",
                "description": "全局开关 - 是否启用主动对话系统功能",
                "default": False,
            },
            "max_proactive_times": {
                "type": "number",
                "description": "最多在你回复之前，AI 主动对话几次",
                "default": 1,
            },
            "enable_visual_preception": {
                "type": "bool",
                "description": "是否启用视觉感知功能（包括窥屏功能）",
                "default": True,
            },
            "enable_topic_creater": {
                "type": "bool",
                "description": "是否启用主动继续对话创造功能",
                "default": False,
            },
            "enable_todo_preception": {
                "type": "bool",
                "description": "是否启用待办事项感知功能",
                "default": False,
            },
            "enable_schedule_reminder": {
                "type": "bool",
                "description": "是否启用日程提醒功能",
                "default": True,
            },
            "enable_important_day_reminder": {
                "type": "bool",
                "description": "是否启用重要日期提醒功能",
                "default": True,
            },
            "todo_weight": {
                "type": "number",
                "description": "待办事项权重（会提醒你的待办事项的概率）",
                "default": -1,
            },
            "topic_weight": {
                "type": "number",
                "description": "话题权重（会主动继续话题的概率）",
                "default": -1,
            },
            "screen_weight": {
                "type": "number",
                "description": "窥屏权重（会窥屏的概率，全选项 -1 会自动监测概率）",
                "default": -1,
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 服务端口
    # ----------------------------------------------------------------------------
    "server": {
        "title": "服务端口",
        "description": "配置各个服务的网络监听地址和端口",
        "settings": {
            "backend_bind_addr": {
                "type": "text",
                "description": "后端监听地址",
                "default": "localhost",
            },
            "backend_port": {
                "type": "number",
                "description": "后端监听端口",
                "default": 8765,
            },
            "frontend_bind_addr": {
                "type": "text",
                "description": "前端监听地址，应该和后端地址同步修改",
                "default": "localhost",
            },
            "frontend_port": {
                "type": "number",
                "description": "前端监听端口，应该和后端端口同步修改",
                "default": 5173,
            },
            "allowed_origins": {
                "type": "text",
                "description": "CORS 配置：允许的源，多个用逗号分隔",
                "default": "",
            },
            "update_url": {
                "type": "text",
                "description": "更新服务地址",
                "default": "lupd.uwaspace.work",
            },
            "community_url": {
                "type": "text",
                "description": "创意工坊地址",
                "default": "http://localhost:5200",
            },
            "backend_access_log": {
                "type": "bool",
                "description": "是否启用后端访问日志",
                "default": True,
            },
            "backend_reload": {
                "type": "bool",
                "description": "是否启用后端热重载（开发模式）",
                "default": False,
            },
            "open_frontend_app": {
                "type": "bool",
                "description": "是否在启动后端时自动打开前端应用",
                "default": True,
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 沙盒功能
    # ----------------------------------------------------------------------------
    "sandbox": {
        "title": "沙盒功能",
        "description": "配置 AI 沙盒环境相关设置",
        "settings": {
            "enable_sandbox_commands": {
                "type": "bool",
                "description": "是否启用沙盒命令执行功能",
                "default": True,
            },
            "simple_tools_max_result_chars": {
                "type": "number",
                "description": "简单工具返回结果的最大字符数",
                "default": 12000,
            },
            "simple_tools_max_rounds": {
                "type": "number",
                "description": "简单工具最大执行轮数",
                "default": 3,
            },
            "simple_tools_planner_timeout": {
                "type": "number",
                "description": "简单工具规划器超时时间（秒）",
                "default": 45,
            },
        },
    },
    # ----------------------------------------------------------------------------
    # 调试与高级
    # ----------------------------------------------------------------------------
    "debug": {
        "title": "调试与高级",
        "description": "调试参数和高级设置",
        "settings": {
            "pipeline_idle_timeout": {
                "type": "number",
                "description": "Pipeline 空闲超时时间（秒）",
                "default": 90,
            },
            "pipeline_cleanup_timeout": {
                "type": "number",
                "description": "Pipeline 清理超时时间（秒）",
                "default": 10,
            },
            "console_show_timestamp": {
                "type": "bool",
                "description": "控制台日志是否显示时间戳",
                "default": False,
            },
            "print_context": {
                "type": "bool",
                "description": "是否把本次发送给 llm 的全部上下文信息截取后打印到终端",
                "default": False,
            },
        },
    },
}
