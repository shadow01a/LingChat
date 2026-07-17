//! 工具规格定义 - 对标 Python spec.py

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

/// 工具处理器 trait
pub trait ToolHandler: Send + Sync {
    /// 执行工具，返回 JSON 结果
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value>;
}

/// 工具规格：名称、描述、参数 schema 和处理器函数
pub struct ToolSpec {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value, // JSON Schema
    pub handler: Arc<dyn ToolHandler>,
}

impl ToolSpec {
    pub fn new<H: ToolHandler + 'static>(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
        handler: H,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            parameters,
            handler: Arc::new(handler),
        }
    }

    /// 转换为 LLM ToolDefinition 格式
    pub fn to_tool_definition(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        })
    }
}

/// 工具调用请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCallRequest {
    pub tool_name: String,
    pub arguments: serde_json::Value,
}

/// 工具调用结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCallResult {
    pub ok: bool,
    pub tool: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

impl ToolCallResult {
    pub fn success(tool: impl Into<String>, result: serde_json::Value) -> Self {
        Self {
            ok: true,
            tool: tool.into(),
            result: Some(result),
            error: None,
        }
    }

    pub fn failure(tool: impl Into<String>, error: impl Into<String>) -> Self {
        Self {
            ok: false,
            tool: tool.into(),
            result: None,
            error: Some(error.into()),
        }
    }
}
