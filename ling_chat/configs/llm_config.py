"""LLM 配置管理器，支持多配置方案存储和切换

LLM 配置已全面迁移至 TOML 文件管理 (configs/llm_configs/*.toml)。
"""

import threading
import tomllib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ling_chat.core.logger import logger
from ling_chat.utils.runtime_path import package_root


class LLMConfig:
    """LLM 配置管理器单例类

    支持多配置方案存储、热切换
    """

    _instance: Optional["LLMConfig"] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> "LLMConfig":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._config_dir: Path = package_root / "configs" / "llm_configs"
        self._active_config_name: str = "default"
        self._config: Dict[str, Any] = {}
        self._callbacks: List[Callable[[], None]] = []

        self._init_config_dir()
        self._load_active()

    def _init_config_dir(self) -> None:
        """初始化配置文件夹"""
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def _load_active(self) -> None:
        """加载当前激活的配置"""
        config_path = self._config_dir / f"{self._active_config_name}.toml"
        if not config_path.exists():
            # 如果激活的配置不存在，回退到 default
            config_path = self._config_dir / "default.toml"
            self._active_config_name = "default"
            if not config_path.exists():
                self._config = self._create_default_config()
                # 写入默认配置文件
                self._write_toml(config_path, self._config)
                logger.info(f"已创建默认 LLM 配置: {config_path}")
                return

        self._config = self._parse_toml(config_path)

    def _parse_toml(self, path: Path) -> Dict[str, Any]:
        """解析 TOML 文件"""
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            logger.error(f"解析 TOML 文件失败 {path}: {e}")
            return self._create_default_config()

    def _write_toml(self, path: Path, config: Dict[str, Any]) -> None:
        """写入 TOML 文件（手动序列化以支持 Python 3.11+）"""
        try:
            lines = []

            # 添加元数据注释
            name = config.get("config_name", "未命名配置")
            desc = config.get("config_description", "")
            lines.append(f'# config_name = "{name}"')
            if desc:
                lines.append(f'# config_description = "{desc}"')
            lines.append("")

            # 写入 main 配置
            if "main" in config:
                lines.append("[main]")
                for key, value in config["main"].items():
                    lines.append(self._format_toml_line(key, value))
                lines.append("")

            # 写入 translator 配置
            if "translator" in config:
                lines.append("[translator]")
                for key, value in config["translator"].items():
                    lines.append(self._format_toml_line(key, value))
                lines.append("")

            # 写入 network 配置（全局网络设置，位于 providers 之前）
            if "network" in config:
                lines.append("[network]")
                for key, value in config["network"].items():
                    lines.append(self._format_toml_line(key, value))
                lines.append("")

            # 写入 providers 配置
            if "providers" in config:
                for provider, pconfig in config["providers"].items():
                    if pconfig:
                        lines.append(f"[providers.{provider}]")
                        for key, value in pconfig.items():
                            lines.append(self._format_toml_line(key, value))
                        lines.append("")

            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            logger.debug(f"已写入 TOML 配置: {path}")
        except Exception as e:
            logger.error(f"写入 TOML 文件失败 {path}: {e}")
            raise

    def _format_toml_line(self, key: str, value: Any) -> str:
        """格式化 TOML 行"""
        if isinstance(value, str):
            if '"' in value:
                return f"{key} = '{value}'"
            return f'{key} = "{value}"'
        elif isinstance(value, bool):
            return f"{key} = {str(value).lower()}"
        elif isinstance(value, (int, float)):
            return f"{key} = {value}"
        return f'{key} = "{value}"'

    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "config_name": "默认配置",
            "config_description": "自动生成的默认配置",
            "main": {
                "provider": "webllm",
                "model": "deepseek-chat",
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "temperature": 1.3,
                "top_p": 0.9,
                "max_tokens": 8192,
                "enable_thinking": "none",
            },
            "translator": {
                "provider": "none",
                "model": "",
                "api_key": "",
                "base_url": "",
            },
            "network": {
                "proxy": "",
            },
            "providers": {},
        }

    def register_reload_callback(self, callback: Callable[[], None]) -> None:
        """注册配置重载回调"""
        self._callbacks.append(callback)

    def _notify_reload(self) -> None:
        """通知所有注册的回调"""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"配置重载回调执行失败: {e}")

    # ============ 公开 API ============

    def get_active_config_name(self) -> str:
        """获取当前激活的配置名称"""
        return self._active_config_name

    def set_active_config(self, name: str) -> bool:
        """切换激活配置

        Args:
            name: 配置方案名称

        Returns:
            是否切换成功
        """
        config_path = self._config_dir / f"{name}.toml"
        if not config_path.exists():
            logger.error(f"配置方案不存在: {name}")
            return False

        self._active_config_name = name
        self._load_active()
        self._notify_reload()
        logger.info(f"已切换 LLM 配置方案: {name}")
        return True

    def get_active_config(self) -> Dict[str, Any]:
        """获取当前激活的完整配置"""
        return self._config.copy()

    def get_main_config(self) -> Dict[str, Any]:
        """获取主对话模型配置（合入默认值，新键自动补全）"""
        config = self._config.get("main", {})
        defaults = self._create_default_config()["main"]
        return {**defaults, **config}

    def get_translator_config(self) -> Dict[str, Any]:
        """获取翻译模型配置

        如果 translator.provider 为 none 或空，返回 main 配置
        """
        trans = self._config.get("translator", {})
        if trans.get("provider", "none") in ["none", ""]:
            return self.get_main_config()
        return trans

    def get_network_config(self) -> Dict[str, Any]:
        """获取全局网络配置（合入默认值，新键自动补全）

        当前包含：
        - proxy: HTTP/HTTPS 代理地址；留空表示走系统代理（trust_env=True）
        """
        defaults = {"proxy": ""}
        config = self._config.get("network", {}) or {}
        return {**defaults, **config}

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取指定提供商的配置"""
        providers = self._config.get("providers", {})
        return providers.get(provider, {})

    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有可用配置方案"""
        configs = []
        for f in sorted(self._config_dir.glob("*.toml")):
            try:
                cfg = self._parse_toml(f)
                configs.append(
                    {
                        "name": f.stem,
                        "display_name": cfg.get("config_name", f.stem),
                        "description": cfg.get("config_description", ""),
                        "is_active": f.stem == self._active_config_name,
                        "main_provider": cfg.get("main", {}).get("provider", ""),
                    }
                )
            except Exception as e:
                logger.warning(f"跳过损坏的配置文件 {f}: {e}")
        return configs

    def get_config(self, name: str) -> Dict[str, Any]:
        """获取指定配置方案的完整内容

        Args:
            name: 配置方案名称

        Raises:
            ValueError: 配置方案不存在
        """
        config_path = self._config_dir / f"{name}.toml"
        if not config_path.exists():
            raise ValueError(f"配置方案不存在: {name}")
        return self._parse_toml(config_path)

    def save_config(self, name: str, config: Dict[str, Any]) -> None:
        """保存/更新配置方案

        Args:
            name: 配置方案名称
            config: 配置字典
        """
        path = self._config_dir / f"{name}.toml"
        self._write_toml(path, config)

        if name == self._active_config_name:
            self._config = config.copy()
            self._notify_reload()

        logger.info(f"已保存 LLM 配置方案: {name}")

    def delete_config(self, name: str) -> None:
        """删除配置方案

        Args:
            name: 配置方案名称（不允许删除 default）

        Raises:
            ValueError: 尝试删除 default 配置
        """
        if name == "default":
            raise ValueError("default 配置不可删除")

        path = self._config_dir / f"{name}.toml"
        if path.exists():
            path.unlink()
            logger.info(f"已删除 LLM 配置方案: {name}")

        # 如果删除的是当前激活配置，切换回 default
        if name == self._active_config_name:
            self.set_active_config("default")

    def get_config_template(self) -> Dict[str, Any]:
        """获取新配置的默认模板"""
        return {
            "config_name": "",
            "config_description": "",
            "main": {
                "provider": "webllm",
                "model": "",
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "temperature": 1.3,
                "top_p": 0.9,
                "max_tokens": 8192,
                "enable_thinking": "none",
            },
            "translator": {
                "provider": "none",
                "model": "",
                "api_key": "",
                "base_url": "",
            },
            "network": {
                "proxy": "",
            },
            "providers": {},
        }

    def reload(self) -> None:
        """热重载配置"""
        self._load_active()
        self._notify_reload()
        logger.info(f"已重载 LLM 配置: {self._active_config_name}")


# 单例实例
llm_config: LLMConfig = LLMConfig()
