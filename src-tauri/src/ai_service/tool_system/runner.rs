//! 工具运行器 - 对标 Python runner.py
//!
//! 核心职责：
//! 1. 关键词匹配快速路由（零延迟）
//! 2. 主 LLM 带工具列表请求，解析 tool_calls
//! 3. 多轮工具调用循环
//! 4. 结果回填到对话上下文

use std::collections::HashMap;
use std::sync::Arc;

use anyhow::{Context, Result};
use serde_json;

use crate::ai_service::llm::LlmConfig;
use crate::ai_service::types::{LlmMessage, ToolDefinition};

use super::registry::ToolRegistry;

/// Chat 模式允许的工具列表（非沙箱工具）
const CHAT_MODE_ALLOWED_TOOLS: &[&str] = &[
    "get_current_status",
    "get_current_scene",
    "get_memory",
    "get_current_time",
    "get_schedules",
    "get_updated_plan",
    "schedule_add_todo",
    "get_memory_notes",
    "memory_add_note",
    "list_scenes",
    "list_characters",
    "switch_scene",
    "switch_character",
];

/// Code 模式允许所有工具
const CODE_MODE_ALL_TOOLS: bool = true;

/// 工具运行器配置
pub struct ToolRunnerConfig {
    pub max_rounds: usize,
    pub max_result_chars: usize,
    pub planner_timeout_seconds: u64,
}

impl Default for ToolRunnerConfig {
    fn default() -> Self {
        Self {
            max_rounds: 3,
            max_result_chars: 12000,
            planner_timeout_seconds: 45,
        }
    }
}

/// 工具运行器
pub struct ToolRunner {
    registry: Arc<ToolRegistry>,
    config: ToolRunnerConfig,
}

impl ToolRunner {
    pub fn new(registry: Arc<ToolRegistry>) -> Self {
        Self {
            registry,
            config: ToolRunnerConfig::default(),
        }
    }

    /// 获取当前模式下允许的 LLM ToolDefinition 列表
    pub fn get_tool_definitions_for_llm(&self, code_mode: bool) -> Vec<ToolDefinition> {
        let names: Option<&[&str]> = if code_mode {
            None
        } else {
            Some(CHAT_MODE_ALLOWED_TOOLS)
        };
        self.registry.to_llm_tool_definitions(names)
    }

    /// 执行工具（公开代理 registry.execute）
    pub async fn execute_tool(
        &self,
        name: &str,
        arguments: serde_json::Value,
    ) -> super::spec::ToolCallResult {
        self.registry.execute(name, arguments).await
    }

    /// 主入口：增强消息上下文
    ///
    /// 在 LLM 生成回复之前，自动调用相关工具获取上下文信息。
    pub async fn enrich_context_if_needed(
        &self,
        messages: Vec<LlmMessage>,
        user_message: String,
        code_mode: bool,
    ) -> Result<Vec<LlmMessage>> {
        if user_message.trim().is_empty() {
            return Ok(messages);
        }

        let mut current_messages = messages;
        let mut executed_tools: Vec<HashMap<String, serde_json::Value>> = Vec::new();

        // 检测是否为沙箱请求或计划跟进请求
        let sandbox_request = self._is_sandbox_request(&user_message);
        let plan_followup_request = self._is_plan_followup_request(&user_message, &current_messages);

        // 第一轮优先使用关键词匹配
        let first_keyword_plan = self._keyword_plan(&user_message);

        // Chat 模式下禁用沙箱工具（除非关键词匹配命中）
        if !code_mode && sandbox_request {
            let keyword_tool = first_keyword_plan
                .as_ref()
                .and_then(|p| p.get("tool"))
                .and_then(|v| v.as_str())
                .unwrap_or("");
            if first_keyword_plan.is_some() && self._is_tool_allowed_in_mode(keyword_tool, false) {
                // 关键词命中，允许执行
            } else {
                // 未命中，返回 chat mode guidance
                return self._with_chat_mode_ide_guidance(current_messages);
            }
        }

        if !code_mode {
            // Chat 模式下不允许计划跟进
        }

        if code_mode {
            // Code 模式下扩大沙箱请求检测范围
        }

        // 计算最大轮次
        let max_rounds = if sandbox_request || plan_followup_request || code_mode {
            self.config.max_rounds.max(if code_mode { 10 } else { 6 })
        } else {
            self.config.max_rounds
        };

        // 多轮工具调用循环
        for round_num in 0..max_rounds {
            // 第一轮且有关键词匹配，优先使用
            let plan = if round_num == 0 {
                first_keyword_plan.clone()
            } else {
                None
            };

            // 如果没有关键词匹配，需要调用 LLM 规划
            let plan = if let Some(p) = plan {
                p
            } else {
                // TODO: 调用 LLM complete_with_tools 进行工具规划
                // 当前简化实现：没有关键词匹配就退出
                break;
            };

            let tool_name = plan
                .get("tool")
                .or(plan.get("name"))
                .or(plan.get("action"))
                .and_then(|v| v.as_str());

            let tool_name = match tool_name {
                Some(name) if !name.is_empty() && name != "none" && name != "null" => name,
                _ => break, // LLM 认为不需要工具
            };

            let arguments = plan
                .get("arguments")
                .or(plan.get("args"))
                .and_then(|v| v.as_object())
                .cloned()
                .unwrap_or_default();

            // 检查工具权限
            if !self._is_tool_allowed_in_mode(tool_name, code_mode) {
                return self._with_chat_mode_ide_guidance(current_messages);
            }

            tracing::info!(
                "[ToolRunner] round {}/{}, running tool {}",
                round_num + 1,
                max_rounds,
                tool_name
            );

            // 执行工具
            let result = self.registry.execute(tool_name, serde_json::Value::Object(arguments.clone())).await;

            // 将结果回填到用户消息末尾（不另开新行）
            let result_text = serde_json::to_string_pretty(&result).unwrap_or_default();
            let result_text = if result_text.len() > self.config.max_result_chars {
                format!("{}...[截断]", &result_text[..self.config.max_result_chars])
            } else {
                result_text
            };

            // 找到最后一条用户消息，将工具结果拼接在后面
            if let Some(last_user) = current_messages.iter_mut().rev().find(|m| m.role == "user") {
                last_user.content.push_str(&format!(
                    "\n\n[工具执行结果 #{}]\n工具: {}\n\
                     以下 JSON 是 LingChat 内部工具系统获取到的数据，请以此为准回答用户。\n\
                     规则：\n\
                     1. 若 JSON 中相关字段为空或 null，说明该项尚未设置。\n\
                     2. 保持正常的 LingChat 对话格式，包含情绪标签。\n\
                     {}",
                    round_num + 1,
                    tool_name,
                    result_text
                ));
            }

            executed_tools.push(HashMap::from([
                ("tool".to_string(), serde_json::json!(tool_name)),
                ("result".to_string(), serde_json::to_value(&result).unwrap_or_default()),
            ]));

            // 检查终止条件
            if self._task_completed(&user_message, &executed_tools, code_mode) {
                break;
            }
        }

        // 如果未执行任何工具，添加 guidance
        if executed_tools.is_empty() && (sandbox_request || plan_followup_request) {
            current_messages.push(LlmMessage {
                role: "user".to_string(),
                content: "[Internal tool guidance]\nThe latest user request is a coding or sandbox task, but no sandbox tool was executed. Do not stream full source code as normal dialogue. Briefly say the sandbox tool call did not complete and ask the user to retry or make the request more specific.".to_string(),
                tool_calls: None,
                tool_call_id: None,
            });
        }

        Ok(current_messages)
    }

    /// 关键词快速路由
    fn _keyword_plan(&self, user_message: &str) -> Option<serde_json::Value> {
        let text = user_message.to_lowercase();

        // 状态查询关键词
        if text.contains("当前状态") || text.contains("现在状态") || text.contains("当前背景")
            || text.contains("现在背景") || text.contains("当前场景") || text.contains("现在场景")
            || text.contains("什么场景") || text.contains("消息数量") || text.contains("当前角色") || text.contains("现在角色")
            || text.contains("状况") || text.contains("调用工具") || text.contains("系统状态")
        {
            return Some(serde_json::json!({
                "tool": "get_current_status",
                "arguments": {}
            }));
        }

        // 当前场景描述
        if text.contains("当前场景描述") || text.contains("现在在哪") || text.contains("在哪里") || text.contains("在什么地方") {
            return Some(serde_json::json!({
                "tool": "get_current_scene",
                "arguments": {}
            }));
        }

        // 时间查询
        if text.contains("现在几点") || text.contains("当前时间") || text.contains("今天几号") || text.contains("现在时间") || text.contains("日期") {
            return Some(serde_json::json!({
                "tool": "get_current_time",
                "arguments": {}
            }));
        }

        // 记忆查询
        if text.contains("记忆笔记") || text.contains("记忆库") || text.contains("手动记忆") || text.contains("保存的记忆") || text.contains("已保存记忆") {
            return Some(serde_json::json!({
                "tool": "get_memory_notes",
                "arguments": {}
            }));
        }

        // 角色记忆
        if text.contains("角色记忆") || text.contains("自动记忆") || text.contains("长期记忆") || text.contains("短期记忆") || text.contains("用户信息") || text.contains("承诺") {
            return Some(serde_json::json!({
                "tool": "get_memory",
                "arguments": {}
            }));
        }

        // 日程查询
        if text.contains("日程") || text.contains("待办") || text.contains("todo") || text.contains("重要日") || text.contains("安排") {
            return Some(serde_json::json!({
                "tool": "get_schedules",
                "arguments": {}
            }));
        }

        // Updated Plan 查询
        if text.contains("updated plan") || text.contains("当前计划") || text.contains("现在计划") || text.contains("计划列表") || text.contains("进度计划") {
            return Some(serde_json::json!({
                "tool": "get_updated_plan",
                "arguments": {}
            }));
        }

        // 场景列表
        if text.contains("有哪些场景") || text.contains("场景列表") || text.contains("可用场景") {
            return Some(serde_json::json!({
                "tool": "list_scenes",
                "arguments": {"limit": 10}
            }));
        }

        // 角色列表
        if text.contains("有哪些角色") || text.contains("角色列表") || text.contains("可用角色") {
            return Some(serde_json::json!({
                "tool": "list_characters",
                "arguments": {"limit": 10}
            }));
        }

        // 切换场景
        if text.contains("切换场景") || text.contains("换场景") || text.contains("去") || text.contains("切换到场景") {
            let scene_name = user_message.split("切换场景").nth(1)
                .or_else(|| user_message.split("换场景").nth(1))
                .or_else(|| user_message.split("去").nth(1))
                .unwrap_or("").trim();
            if !scene_name.is_empty() {
                return Some(serde_json::json!({
                    "tool": "switch_scene",
                    "arguments": {"scene_name": scene_name}
                }));
            }
        }

        // 切换角色
        if text.contains("切换角色") || text.contains("换角色") || text.contains("变成") || text.contains("切换到角色") {
            let char_name = user_message.split("切换角色").nth(1)
                .or_else(|| user_message.split("换角色").nth(1))
                .or_else(|| user_message.split("变成").nth(1))
                .unwrap_or("").trim();
            if !char_name.is_empty() {
                return Some(serde_json::json!({
                    "tool": "switch_character",
                    "arguments": {"character_name": char_name}
                }));
            }
        }

        None
    }

    /// 检测是否为沙箱请求
    fn _is_sandbox_request(&self, user_message: &str) -> bool {
        let text = user_message.to_lowercase();

        // 直接代码术语
        let direct_code_terms = ["代码", "编程", "脚本", "沙盒", "python", "javascript", "typescript", "pygame", "html", "css", "node", "npm", "pnpm", "game"];
        if direct_code_terms.iter().any(|t| text.contains(t)) {
            return true;
        }

        // 动作术语 + 目标术语组合
        let action_terms = ["写一个", "写个", "创建", "新建", "保存", "运行", "执行", "测试", "修改", "编辑"];
        let target_terms = ["程序", "文件", "游戏", "项目", "命令", "目录", "网页"];

        action_terms.iter().any(|a| text.contains(a)) && target_terms.iter().any(|t| text.contains(t))
    }

    /// 检测是否为计划跟进请求
    fn _is_plan_followup_request(&self, user_message: &str, messages: &[LlmMessage]) -> bool {
        let text_lower = user_message.to_lowercase();
        let text = text_lower.trim();

        if text.contains("plan") || text.contains("计划") || text.contains("下一步") {
            return true;
        }

        if text == "继续" || text == "继续吧" || text == "继续执行" || text == "继续完成" || text == "接着" || text == "接着做" {
            // 检查最近的消息是否有 plan 相关
            let recent = messages.iter().rev().take(3)
                .map(|m| m.content.to_lowercase())
                .collect::<Vec<_>>()
                .join(" ");

            return recent.contains("plan") || recent.contains("计划") || recent.contains("sandbox");
        }

        false
    }

    /// 检查工具是否在允许模式中
    fn _is_tool_allowed_in_mode(&self, tool_name: &str, code_mode: bool) -> bool {
        if code_mode {
            return true;
        }
        CHAT_MODE_ALLOWED_TOOLS.contains(&tool_name)
    }

    /// Chat 模式 IDE 指引
    fn _with_chat_mode_ide_guidance(&self, messages: Vec<LlmMessage>) -> Result<Vec<LlmMessage>> {
        let mut messages = messages;
        messages.push(LlmMessage {
            role: "user".to_string(),
            content: "[Internal tool policy]\nChat mode has AI IDE tools disabled. Do not use sandbox, file editing, command execution, or update_plan tools in chat mode. If the user wants coding, sandbox, file, command, or IDE-style plan work, briefly ask them to switch on Code mode. Non-programming LingChat tools such as memory, schedules, current status, scenes, and character switching remain available.".to_string(),
            tool_calls: None,
            tool_call_id: None,
        });
        Ok(messages)
    }

    /// 检查任务是否完成
    fn _task_completed(&self, user_message: &str, executed_tools: &[HashMap<String, serde_json::Value>], code_mode: bool) -> bool {
        if executed_tools.is_empty() {
            return false;
        }

        // 简单判断：如果有工具执行成功，认为完成
        // TODO: 更复杂的完成条件判断逻辑
        true
    }
}
