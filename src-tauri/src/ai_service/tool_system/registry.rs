//! 工具注册表 - 对标 Python registry.py
//!
//! 聚合所有工具提供者，提供统一的注册、查询和执行接口。

use std::collections::HashMap;
use std::sync::Arc;

use serde_json;

use crate::ai_service::types::ToolDefinition;
use super::spec::{ToolCallResult, ToolSpec};

/// 工具注册中心
pub struct ToolRegistry {
    tools: HashMap<String, Arc<ToolSpec>>,
}

impl ToolRegistry {
    pub fn new() -> Self {
        let mut registry = Self {
            tools: HashMap::new(),
        };
        registry.register_all();
        registry
    }

    /// 注册所有工具提供者
    fn register_all(&mut self) {
        // 状态查询工具
        for spec in super::status_tools::get_status_tools() {
            self.tools.insert(spec.name.clone(), Arc::new(spec));
        }

        // 日程计划工具
        for spec in super::schedule_tools::get_schedule_tools() {
            self.tools.insert(spec.name.clone(), Arc::new(spec));
        }

        // 记忆管理工具
        for spec in super::memory_tools::get_memory_tools() {
            self.tools.insert(spec.name.clone(), Arc::new(spec));
        }

        // 场景角色工具
        for spec in super::scene_character_tools::get_scene_character_tools() {
            self.tools.insert(spec.name.clone(), Arc::new(spec));
        }

        // 沙箱操作工具
        for spec in super::sandbox_tools::get_sandbox_tools() {
            self.tools.insert(spec.name.clone(), Arc::new(spec));
        }
    }

    /// 获取所有工具名称
    pub fn tool_names(&self) -> Vec<&str> {
        self.tools.keys().map(|s| s.as_str()).collect()
    }

    /// 获取指定工具的规格
    #[allow(dead_code)]
    pub fn get_spec(&self, name: &str) -> Option<&ToolSpec> {
        self.tools.get(name).map(|arc| arc.as_ref())
    }

    /// 获取工具规格列表（用于 LLM prompt）
    pub fn get_tool_definitions(&self, names: Option<&[&str]>) -> Vec<serde_json::Value> {
        if let Some(names) = names {
            self.tools
                .iter()
                .filter(|(name, _)| names.contains(&name.as_str()))
                .map(|(_, spec)| spec.to_tool_definition())
                .collect()
        } else {
            self.tools
                .values()
                .map(|spec| spec.to_tool_definition())
                .collect()
        }
    }

    /// 获取 LLM 可直接使用的 ToolDefinition 列表（typed）
    pub fn to_llm_tool_definitions(&self, names: Option<&[&str]>) -> Vec<ToolDefinition> {
        let specs: Vec<&ToolSpec> = if let Some(names) = names {
            names.iter()
                .filter_map(|n| self.tools.get(*n))
                .map(|a| a.as_ref())
                .collect()
        } else {
            self.tools.values().map(|a| a.as_ref()).collect()
        };

        specs.into_iter().map(|spec| {
            ToolDefinition::new(
                &spec.name,
                &spec.description,
                spec.parameters.clone(),
            )
        }).collect()
    }

    /// 执行工具
    pub async fn execute(&self, name: &str, arguments: serde_json::Value) -> ToolCallResult {
        let spec = match self.tools.get(name) {
            Some(s) => s,
            None => {
                return ToolCallResult::failure(
                    name,
                    format!("Unknown tool: {}. Available: {:?}", name, self.tool_names()),
                )
            }
        };

        match spec.handler.execute(&arguments) {
            Ok(result) => ToolCallResult::success(name, result),
            Err(e) => ToolCallResult::failure(name, e.to_string()),
        }
    }
}

impl Default for ToolRegistry {
    fn default() -> Self {
        Self::new()
    }
}
