"""环境变量配置 API（已全面迁移至 TOML 配置）

之前的 .env 文件解析/保存逻辑已完全移除，转为由 RuntimeConfig 管理 TOML 配置。
前后端 API 接口和返回格式保持不变。

迁移记录：
- 配置文件: configs/runtime_configs/default.toml
- 配置元数据: configs/runtime_schema.toml
- 配置管理器: configs/runtime_config.py
"""

from typing import Dict

from fastapi import APIRouter, Body, HTTPException

from ling_chat.configs.runtime_config import runtime_config
from ling_chat.utils.runtime_config import apply_runtime_config_changes


def parse_env_file():
    """
    解析配置文件（已从 .env 迁移至 TOML）。
    返回与原来相同格式的结构化数据。
    """
    return runtime_config.get_settings_structured()


def save_env_file(new_values: Dict[str, str]):
    """
    保存配置（已从 .env 迁移至 TOML）。
    """
    runtime_config.save_settings(new_values)


router = APIRouter(prefix="/api/v1/chat/config", tags=["Chat Env Config"])


@router.get("/key/{key}")
async def get_single_config(key: str):
    """
    根据环境变量名（key）获取其当前值及描述信息。
    若找不到则返回 404。
    """
    try:
        full_config = parse_env_file()
        for category in full_config.values():
            for sub in category["subcategories"].values():
                for setting in sub["settings"]:
                    if setting["key"] == key:
                        return setting
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read config: {str(e)}"
        ) from e


@router.get("/settings")
async def get_settings():
    try:
        config = parse_env_file()
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while parsing config: {str(e)}",
        ) from e


@router.patch("/settings")
async def save_config(new_values: Dict[str, str] = Body(...)):  # noqa: B008
    try:
        save_env_file(new_values)
        # 保存后触发运行时热更新
        apply_runtime_config_changes(new_values)
        return {"status": "success", "message": "配置已成功保存并已生效！"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save config: {str(e)}"
        ) from e
