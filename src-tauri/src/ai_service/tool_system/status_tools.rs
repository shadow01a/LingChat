//! 状态查询工具 - 对标 Python status_tools.py

use anyhow::Result;
use chrono::Local;
use serde_json;

use super::spec::{ToolHandler, ToolSpec};

/// 获取所有状态查询工具
pub fn get_status_tools() -> Vec<ToolSpec> {
    vec![
        ToolSpec::new(
            "get_current_status",
            "读取 LingChat 当前运行时状态，包括当前角色、场景、背景和消息数量。",
            serde_json::json!({
                "type": "object",
                "properties": {},
                "additionalProperties": false
            }),
            GetStatusHandler,
        ),
        ToolSpec::new(
            "get_current_scene",
            "读取当前场景描述和角色所在的场景名称。",
            serde_json::json!({
                "type": "object",
                "properties": {},
                "additionalProperties": false
            }),
            GetSceneHandler,
        ),
        ToolSpec::new(
            "get_current_time",
            "获取当前日期和时间。",
            serde_json::json!({
                "type": "object",
                "properties": {},
                "additionalProperties": false
            }),
            GetTimeHandler,
        ),
    ]
}

// ─── 具体处理器实现 ────────────────────────────────────────

struct GetStatusHandler;
impl ToolHandler for GetStatusHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        // TODO: 需要从 runtime 获取 GameStatus
        // 当前返回占位数据
        Ok(serde_json::json!({
            "ok": true,
            "data": {
                "current_character": null,
                "player": {"user_name": "Player"},
                "scene": {"current_scene": "default", "scene_description": ""},
                "media": {"background": "", "background_effect": "", "background_music": ""},
                "message_count": 0
            }
        }))
    }
}

struct GetSceneHandler;
impl ToolHandler for GetSceneHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({
            "ok": true,
            "data": {
                "current_scene": "default",
                "scene_description": "默认场景"
            }
        }))
    }
}

struct GetTimeHandler;
impl ToolHandler for GetTimeHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        let now = Local::now();
        Ok(serde_json::json!({
            "ok": true,
            "data": {
                "datetime": now.to_rfc3339(),
                "date": now.format("%Y-%m-%d").to_string(),
                "time": now.format("%H:%M:%S").to_string(),
                "weekday": now.format("%A").to_string()
            }
        }))
    }
}
