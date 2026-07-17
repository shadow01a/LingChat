//! 工具系统模块 - agent_tools 的 Rust 实现
//!
//! 提供工具调用能力，让 LLM 可以：
//! - 查询/修改游戏状态（场景、角色、记忆、日程）
//! - 沙箱化文件操作和代码执行

pub mod registry;
pub mod runner;
pub mod sandbox;
pub mod spec;
pub mod status_tools;
pub mod schedule_tools;
pub mod memory_tools;
pub mod scene_character_tools;
pub mod sandbox_tools;

pub use registry::ToolRegistry;
pub use runner::ToolRunner;
pub use sandbox::{sandbox_read_file, sandbox_write_file, sandbox_list_files, sandbox_delete_file, sandbox_execute_command};
