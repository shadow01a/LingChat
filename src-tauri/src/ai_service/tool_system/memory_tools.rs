//! 记忆管理工具 - 对标 Python memory_tools.py

use anyhow::Result;
use serde_json;

use super::spec::{ToolHandler, ToolSpec};

pub fn get_memory_tools() -> Vec<ToolSpec> {
    vec![
        ToolSpec::new(
            "get_memory_notes",
            "仅读取从日程记忆面板手动保存的 LingChat 记忆笔记。",
            serde_json::json!({
                "type": "object",
                "properties": {},
                "additionalProperties": false
            }),
            GetMemoryNotesHandler,
        ),
        ToolSpec::new(
            "memory_add_note",
            "向日程记忆面板中添加持久的手动记忆笔记。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "记忆笔记内容"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "可选的标签列表"
                    },
                    "source": {"type": "string", "description": "可选的来源标签"}
                },
                "required": ["content"],
                "additionalProperties": false
            }),
            MemoryAddNoteHandler,
        ),
    ]
}

struct GetMemoryNotesHandler;
impl ToolHandler for GetMemoryNotesHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({
            "ok": true,
            "path": "game_data/schedules.json",
            "count": 0,
            "items": []
        }))
    }
}

struct MemoryAddNoteHandler;
impl ToolHandler for MemoryAddNoteHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let content = args.get("content").and_then(|v| v.as_str()).unwrap_or("");
        if content.is_empty() {
            return Ok(serde_json::json!({
                "ok": false,
                "error": "content is required"
            }));
        }
        // TODO: 实际写入 schedules.json
        Ok(serde_json::json!({
            "ok": true,
            "content": content,
            "message": "Memory note added (placeholder)"
        }))
    }
}
