"""运行时配置热重载处理

配置已全面迁移至 TOML 文件管理：
- LLM 配置: configs/llm_configs/*.toml
- 运行时配置: configs/runtime_configs/*.toml
"""

import threading
from typing import Dict

from ling_chat.configs.llm_config import llm_config
from ling_chat.configs.runtime_config import runtime_config
from ling_chat.core.service_manager import service_manager

_runtime_update_lock = threading.Lock()

# LLM 相关配置 key（用于触发热重载）
LLM_CONFIG_KEYS = {
    "LLM_PROVIDER",
    "MODEL_TYPE",
    "CHAT_API_KEY",
    "CHAT_BASE_URL",
    "TEMPERATURE",
    "TOP_P",
    "ENABLE_THINKING",
    "TRANSLATE_LLM_PROVIDER",
    "TRANSLATE_MODEL",
    "TRANSLATE_API_KEY",
    "TRANSLATE_BASE_URL",
}


def apply_runtime_config_changes(new_values: Dict[str, str]) -> None:
    """应用运行时配置更改，支持热重载"""
    with _runtime_update_lock:
        # 检测是否有 LLM 配置变更
        has_llm_changes = any(key in LLM_CONFIG_KEYS for key in new_values.keys())

        # 如果有 LLM 配置变更，触发 LLMConfig 重载
        if has_llm_changes:
            llm_config.reload()

        # 触发 RuntimeConfig 重载
        runtime_config.reload()

        # 通知 AIService 应用配置更改
        ai_service = service_manager.ai_service
        if ai_service is not None:
            ai_service.apply_runtime_config(new_values)
