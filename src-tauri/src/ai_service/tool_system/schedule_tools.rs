//! 日程计划工具 - 对标 Python schedule_tools.py

use anyhow::Result;
use serde_json;

use super::spec::{ToolHandler, ToolSpec};

pub fn get_schedule_tools() -> Vec<ToolSpec> {
    vec![
        ToolSpec::new(
            "get_schedules",
            "从本地 LingChat 日程数据中读取日程、待办和重要日子。",
            serde_json::json!({
                "type": "object",
                "properties": {},
                "additionalProperties": false
            }),
            GetSchedulesHandler,
        ),
        ToolSpec::new(
            "get_updated_plan",
            "读取 LingChat 当前的 Updated Plan。",
            serde_json::json!({
                "type": "object",
                "properties": {},
                "additionalProperties": false
            }),
            GetUpdatedPlanHandler,
        ),
        ToolSpec::new(
            "update_plan",
            "用带步骤和状态的清单替换 LingChat 当前的 Updated Plan。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "可选的计划标题"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step": {"type": "string", "description": "计划步骤内容"},
                                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                                "note": {"type": "string", "description": "可选的简短备注"}
                            },
                            "required": ["step"]
                        }
                    },
                    "source": {"type": "string", "description": "可选的来源标签，默认为 AI"}
                },
                "required": ["items"],
                "additionalProperties": false
            }),
            UpdatePlanHandler,
        ),
        ToolSpec::new(
            "schedule_add_todo",
            "向 LingChat 日程/待办数据中添加待办事项。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要添加的待办内容"},
                    "group_title": {"type": "string", "description": "可选的待办分组标题，默认为'AI 添加'"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 5, "description": "优先级"},
                    "deadline": {"type": "string", "description": "可选的截止时间文本或日期"}
                },
                "required": ["text"],
                "additionalProperties": false
            }),
            ScheduleAddTodoHandler,
        ),
    ]
}

struct GetSchedulesHandler;
impl ToolHandler for GetSchedulesHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({
            "ok": true,
            "data": {
                "scheduleGroups": {},
                "todoGroups": {},
                "importantDays": [],
                "memoryNotes": [],
                "updatedPlan": null
            }
        }))
    }
}

struct GetUpdatedPlanHandler;
impl ToolHandler for GetUpdatedPlanHandler {
    fn execute(&self, _args: &serde_json::Value) -> Result<serde_json::Value> {
        Ok(serde_json::json!({
            "ok": true,
            "plan": null,
            "item_count": 0
        }))
    }
}

struct UpdatePlanHandler;
impl ToolHandler for UpdatePlanHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        // TODO: 实际写入 schedules.json
        Ok(serde_json::json!({
            "ok": true,
            "message": "Plan updated (placeholder)"
        }))
    }
}

struct ScheduleAddTodoHandler;
impl ToolHandler for ScheduleAddTodoHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let text = args.get("text").and_then(|v| v.as_str()).unwrap_or("");
        if text.is_empty() {
            return Ok(serde_json::json!({
                "ok": false,
                "error": "text is required"
            }));
        }
        // TODO: 实际写入 schedules.json
        Ok(serde_json::json!({
            "ok": true,
            "text": text,
            "message": "Todo added (placeholder)"
        }))
    }
}
