//! 场景角色工具 - 对标 Python scene_character_tools.py

use anyhow::Result;
use serde_json;

use super::spec::{ToolHandler, ToolSpec};

pub fn get_scene_character_tools() -> Vec<ToolSpec> {
    vec![
        ToolSpec::new(
            "list_scenes",
            "列出可用的 LingChat 场景及其描述。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20}
                },
                "additionalProperties": false
            }),
            ListScenesHandler,
        ),
        ToolSpec::new(
            "list_characters",
            "列出已知的 LingChat 角色。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20}
                },
                "additionalProperties": false
            }),
            ListCharactersHandler,
        ),
        ToolSpec::new(
            "switch_scene",
            "切换到不同的场景。通过场景名称或部分名称匹配。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "scene_name": {"type": "string", "description": "要切换到的场景名称或部分名称"}
                },
                "required": ["scene_name"],
                "additionalProperties": false
            }),
            SwitchSceneHandler,
        ),
        ToolSpec::new(
            "switch_character",
            "切换到不同的角色。通过角色名称或部分名称匹配。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "character_name": {"type": "string", "description": "要切换到的角色名称或部分名称"}
                },
                "required": ["character_name"],
                "additionalProperties": false
            }),
            SwitchCharacterHandler,
        ),
    ]
}

struct ListScenesHandler;
impl ToolHandler for ListScenesHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({
            "ok": true,
            "count": 0,
            "items": []
        }))
    }
}

struct ListCharactersHandler;
impl ToolHandler for ListCharactersHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({
            "ok": true,
            "count": 0,
            "items": []
        }))
    }
}

struct SwitchSceneHandler;
impl ToolHandler for SwitchSceneHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let scene_name = args.get("scene_name").and_then(|v| v.as_str()).unwrap_or("");
        if scene_name.is_empty() {
            return Ok(serde_json::json!({
                "ok": false,
                "error": "scene_name is required"
            }));
        }
        // TODO: 实际切换场景
        Ok(serde_json::json!({
            "ok": true,
            "scene": {"sceneName": scene_name},
            "message": format!("Switched to scene: {}", scene_name)
        }))
    }
}

struct SwitchCharacterHandler;
impl ToolHandler for SwitchCharacterHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let char_name = args.get("character_name").and_then(|v| v.as_str()).unwrap_or("");
        if char_name.is_empty() {
            return Ok(serde_json::json!({
                "ok": false,
                "error": "character_name is required"
            }));
        }
        // TODO: 实际切换角色
        Ok(serde_json::json!({
            "ok": true,
            "character": {"name": char_name},
            "message": format!("Switched to character: {}", char_name)
        }))
    }
}
