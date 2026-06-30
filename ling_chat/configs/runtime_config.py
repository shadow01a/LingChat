"""运行时配置管理器（替代 .env）

从 configs/runtime_configs/*.toml 加载配置，支持热重载。
Schema 定义在 Python 文件中，避免打包时 TOML 文件未加入的问题。
"""

import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from ling_chat.configs.runtime_schema import RUNTIME_SCHEMA
from ling_chat.utils.runtime_path import package_root


class RuntimeConfig:
    """运行时配置管理器

    从 configs/runtime_configs/*.toml 加载配置，支持热重载
    """

    _instance: Optional["RuntimeConfig"] = None

    def __new__(cls) -> "RuntimeConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self._config_dir: Path = package_root / "configs" / "runtime_configs"
        self._config: Dict[str, Any] = {}
        # 直接使用 Python schema
        self._schema = RUNTIME_SCHEMA

        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._load_config()

    def _load_config(self) -> None:
        """加载默认配置，首次启动时从 schema 默认值自动生成"""
        config_path = self._config_dir / "default.toml"
        if config_path.exists():
            with open(config_path, "rb") as f:
                self._config = tomllib.load(f)
        else:
            # 首次启动，从 schema 默认值自动生成 default.toml
            self._generate_default_from_schema()
            self._save_config()

    def _generate_default_from_schema(self) -> None:
        """从 schema 中的 default 值生成默认配置"""
        self._config = {}
        for section_name, section_data in self._schema.items():
            self._config[section_name] = {}
            settings = section_data.get("settings", {})
            for key, meta in settings.items():
                self._config[section_name][key] = meta.get("default")

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key_path: 点分隔的路径，如 "log.log_level"
            default: 默认值

        Returns:
            配置值或默认值
        """
        parts = key_path.split(".")
        value = self._config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # 尝试从 schema 获取默认值
                if len(parts) == 2 and default is None:
                    section, key = parts
                    if section in self._schema:
                        settings = self._schema[section].get("settings", {})
                        if key in settings:
                            return settings[key].get("default")
                return default
        return value

    def get_by_env_key(self, env_key: str, default: Any = None) -> Any:
        """通过环境变量键名获取配置值（用于兼容旧代码）

        映射关系：ENV_KEY -> section.key（小写转换）
        """
        for section_name, section_data in self._schema.items():
            settings = section_data.get("settings", {})
            for key in settings.keys():
                if key.upper() == env_key:
                    value = self.get(f"{section_name}.{key}")
                    return value if value is not None else default

        # 未找到映射，返回默认值
        return default

    def set(self, key_path: str, value: Any) -> None:
        """设置配置值（运行时）"""
        parts = key_path.split(".")
        config = self._config
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        config[parts[-1]] = value

    def reload(self) -> None:
        """重载配置"""
        self._load_config()

    def to_flat_dict(self) -> Dict[str, Any]:
        """展平配置为 {ENV_KEY: value} 格式，用于向后兼容"""
        result = {}
        self._flatten_dict(self._config, "", result)
        return result

    def _flatten_dict(self, d: Dict, prefix: str, result: Dict) -> None:
        """递归展平嵌套字典"""
        for key, value in d.items():
            full_key = f"{prefix}_{key}".upper() if prefix else key.upper()
            if isinstance(value, dict):
                self._flatten_dict(value, full_key, result)
            else:
                result[full_key] = value

    def get_settings_structured(self) -> Dict[str, Any]:
        """获取结构化配置数据（与 parse_env_file 格式一致，用于前端 API）"""
        structured_config = {}
        config = self._config

        for section_name, section_data in self._schema.items():
            category_key = section_data.get("title", section_name)

            if category_key not in structured_config:
                structured_config[category_key] = {"subcategories": {}}

            subcategory_name = section_data.get("title", section_name)
            subcategory_desc = section_data.get("description", "")

            structured_config[category_key]["subcategories"][subcategory_name] = {
                "description": subcategory_desc,
                "settings": [],
            }

            settings_meta = section_data.get("settings", {})
            for key, meta in settings_meta.items():
                # 从配置中获取值，若无则用默认值
                value = config.get(section_name, {}).get(key, meta.get("default"))

                structured_config[category_key]["subcategories"][subcategory_name][
                    "settings"
                ].append(
                    {
                        "key": key.upper(),
                        "value": str(value),
                        "description": meta.get("description", ""),
                        "type": meta.get("type", "text"),
                    }
                )

        return structured_config

    def save_settings(self, new_values: Dict[str, str]) -> None:
        """保存配置（从前端 API 接收的键值对）"""
        # 将扁平的键值对转换回嵌套结构并保存
        for env_key, value_str in new_values.items():
            for section_name, section_data in self._schema.items():
                settings_meta = section_data.get("settings", {})
                for key in settings_meta.keys():
                    if key.upper() == env_key:
                        # 解析值类型
                        meta = settings_meta[key]
                        value_type = meta.get("type", "text")
                        value = self._parse_value(value_str, value_type)

                        # 设置值
                        self.set(f"{section_name}.{key}", value)
                        break

        # 写入 TOML 文件
        self._save_config()

    def _parse_value(self, value_str: str, value_type: str) -> Any:
        """根据类型解析字符串值"""
        if value_type == "bool":
            return value_str.lower() in ("true", "1", "yes")
        elif value_type == "number":
            try:
                return int(value_str)
            except ValueError:
                return float(value_str)
        else:
            return value_str

    def _save_config(self) -> None:
        """将当前配置写入 default.toml"""
        config_path = self._config_dir / "default.toml"

        lines = []
        for section_name, section_data in self._schema.items():
            lines.append(f"[{section_name}]")

            settings_meta = section_data.get("settings", {})
            for key in settings_meta.keys():
                value = self._config.get(section_name, {}).get(key)
                lines.append(self._format_toml_line(key, value))

            lines.append("")

        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _format_toml_line(self, key: str, value: Any) -> str:
        """格式化 TOML 行"""
        if value is None:
            return f'{key} = ""'
        if isinstance(value, str):
            if '"' in value:
                return f"{key} = '{value}'"
            return f'{key} = "{value}"'
        elif isinstance(value, bool):
            return f"{key} = {str(value).lower()}"
        elif isinstance(value, (int, float)):
            return f"{key} = {value}"
        return f'{key} = "{value}"'


# 单例实例
runtime_config: RuntimeConfig = RuntimeConfig()
