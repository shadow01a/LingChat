//! 沙箱操作工具 - 对标 Python sandbox_tools.py

use anyhow::Result;
use serde_json;

use super::spec::{ToolHandler, ToolSpec};
use super::sandbox::{sandbox_read_file, sandbox_write_file, sandbox_list_files, sandbox_delete_file, sandbox_execute_command};

pub fn get_sandbox_tools() -> Vec<ToolSpec> {
    vec![
        ToolSpec::new(
            "sandbox_read_file",
            "读取沙盒内文件内容。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件相对路径"}
                },
                "required": ["path"],
                "additionalProperties": false
            }),
            SandboxReadFileHandler,
        ),
        ToolSpec::new(
            "sandbox_write_file",
            "写入内容到沙盒文件。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件相对路径"},
                    "content": {"type": "string", "description": "文件内容"},
                    "append": {"type": "boolean", "description": "是否追加模式，默认 false"}
                },
                "required": ["path", "content"],
                "additionalProperties": false
            }),
            SandboxWriteFileHandler,
        ),
        ToolSpec::new(
            "sandbox_list_files",
            "列出沙盒目录内的文件。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录相对路径，默认 '.'"}
                },
                "additionalProperties": false
            }),
            SandboxListFilesHandler,
        ),
        ToolSpec::new(
            "sandbox_delete_file",
            "删除沙盒内文件。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件相对路径"},
                    "recursive": {"type": "boolean", "description": "是否递归删除，默认 false"}
                },
                "required": ["path"],
                "additionalProperties": false
            }),
            SandboxDeleteFileHandler,
        ),
        ToolSpec::new(
            "sandbox_execute_command",
            "在沙盒内执行命令。",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                    "timeout": {"type": "integer", "description": "超时秒数，默认 30"}
                },
                "required": ["command"],
                "additionalProperties": false
            }),
            SandboxExecuteCommandHandler,
        ),
    ]
}

struct SandboxReadFileHandler;
impl ToolHandler for SandboxReadFileHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let path = args.get("path").and_then(|v| v.as_str()).unwrap_or("");
        let result = sandbox_read_file(path);
        Ok(serde_json::to_value(result)?)
    }
}

struct SandboxWriteFileHandler;
impl ToolHandler for SandboxWriteFileHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let path = args.get("path").and_then(|v| v.as_str()).unwrap_or("");
        let content = args.get("content").and_then(|v| v.as_str()).unwrap_or("");
        let append = args.get("append").and_then(|v| v.as_bool()).unwrap_or(false);
        let result = sandbox_write_file(path, content, append);
        Ok(serde_json::to_value(result)?)
    }
}

struct SandboxListFilesHandler;
impl ToolHandler for SandboxListFilesHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let path = args.get("path").and_then(|v| v.as_str()).unwrap_or(".");
        let result = sandbox_list_files(path);
        Ok(serde_json::to_value(result)?)
    }
}

struct SandboxDeleteFileHandler;
impl ToolHandler for SandboxDeleteFileHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let path = args.get("path").and_then(|v| v.as_str()).unwrap_or("");
        let recursive = args.get("recursive").and_then(|v| v.as_bool()).unwrap_or(false);
        let result = sandbox_delete_file(path, recursive);
        Ok(serde_json::to_value(result)?)
    }
}

struct SandboxExecuteCommandHandler;
impl ToolHandler for SandboxExecuteCommandHandler {
    fn execute(&self, args: &serde_json::Value) -> Result<serde_json::Value> {
        let command = args.get("command").and_then(|v| v.as_str()).unwrap_or("");
        let timeout = args.get("timeout").and_then(|v| v.as_u64()).unwrap_or(30);
        let result = sandbox_execute_command(command, timeout);
        Ok(serde_json::to_value(result)?)
    }
}
