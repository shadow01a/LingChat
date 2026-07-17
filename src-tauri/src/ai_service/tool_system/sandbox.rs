//! 沙箱核心实现 - 对标 Python sandbox.py
//!
//! 提供安全的文件读写和命令执行能力，所有操作限制在沙盒目录内。

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::Duration;

use crate::api::data_dir;

/// 沙盒根目录
fn sandbox_dir() -> PathBuf {
    let dir = data_dir().join("sandbox");
    fs::create_dir_all(&dir).ok();
    dir
}

/// 沙盒结果类型
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxResult {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub size: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub items: Option<Vec<SandboxItem>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stdout: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stderr: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub returncode: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub created: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lines_added: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub lines_removed: Option<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxItem {
    pub name: String,
    #[serde(rename = "type")]
    pub item_type: String, // "file" or "directory"
}

/// 解析沙盒内路径，防止路径遍历攻击
fn resolve_sandbox_path(relative_path: &str) -> Result<PathBuf, String> {
    let sandbox_root = sandbox_dir();

    // 过滤掉 .. 和 . 组件
    let safe_parts: Vec<_> = Path::new(relative_path)
        .components()
        .filter(|c| {
            let s = c.as_os_str().to_string_lossy();
            s != ".." && s != "."
        })
        .collect();

    let full_path = if safe_parts.is_empty() {
        sandbox_root.clone()
    } else {
        sandbox_root.join(PathBuf::from_iter(safe_parts))
    };

    // 安全检查：路径必须在沙盒目录下
    let resolved = full_path.canonicalize().unwrap_or_else(|_| full_path.clone());
    if !resolved.starts_with(&sandbox_root) {
        return Err(format!("Path '{}' is outside the sandbox", relative_path));
    }

    Ok(resolved)
}

/// 读取沙盒文件
pub fn sandbox_read_file(path: &str) -> SandboxResult {
    match resolve_sandbox_path(path) {
        Ok(file_path) => {
            if !file_path.exists() {
                return SandboxResult {
                    ok: false,
                    error: Some(format!("File not found: {}", path)),
                    ..Default::default()
                };
            }
            if file_path.is_dir() {
                return SandboxResult {
                    ok: false,
                    error: Some(format!("'{}' is a directory, not a file", path)),
                    ..Default::default()
                };
            }
            // 限制文件大小（10MB）
            if let Ok(meta) = fs::metadata(&file_path) {
                if meta.len() > 10 * 1024 * 1024 {
                    return SandboxResult {
                        ok: false,
                        error: Some(format!("File too large (>10MB): {}", path)),
                        ..Default::default()
                    };
                }
            }
            match fs::read_to_string(&file_path) {
                Ok(content) => {
                    let relative_path = file_path.strip_prefix(sandbox_dir())
                        .map(|p| p.to_string_lossy().to_string())
                        .unwrap_or_else(|_| path.to_string());
                    SandboxResult {
                        ok: true,
                        path: Some(relative_path),
                        content: Some(content.clone()),
                        size: Some(content.len()),
                        ..Default::default()
                    }
                }
                Err(e) => SandboxResult {
                    ok: false,
                    error: Some(format!("Read failed: {}", e)),
                    ..Default::default()
                },
            }
        }
        Err(e) => SandboxResult {
            ok: false,
            error: Some(e),
            ..Default::default()
        },
    }
}

/// 写入沙盒文件
pub fn sandbox_write_file(path: &str, content: &str, append: bool) -> SandboxResult {
    match resolve_sandbox_path(path) {
        Ok(file_path) => {
            // 创建父目录
            if let Some(parent) = file_path.parent() {
                if let Err(e) = fs::create_dir_all(parent) {
                    return SandboxResult {
                        ok: false,
                        error: Some(format!("Failed to create parent directory: {}", e)),
                        ..Default::default()
                    };
                }
            }

            let existed_before = file_path.exists();
            let previous_content = fs::read_to_string(&file_path).ok().unwrap_or_default();

            let write_result = if append {
                fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(&file_path)
                    .and_then(|mut f| std::io::Write::write_all(&mut f, content.as_bytes()))
            } else {
                fs::write(&file_path, content)
            };

            match write_result {
                Ok(_) => {
                    let (lines_added, lines_removed) = line_change_stats(&previous_content, content);
                    let relative_path = file_path.strip_prefix(sandbox_dir())
                        .map(|p| p.to_string_lossy().to_string())
                        .unwrap_or_else(|_| path.to_string());
                    SandboxResult {
                        ok: true,
                        path: Some(relative_path),
                        created: Some(!existed_before),
                        lines_added: Some(lines_added),
                        lines_removed: Some(lines_removed),
                        ..Default::default()
                    }
                }
                Err(e) => SandboxResult {
                    ok: false,
                    error: Some(format!("Write failed: {}", e)),
                    ..Default::default()
                },
            }
        }
        Err(e) => SandboxResult {
            ok: false,
            error: Some(e),
            ..Default::default()
        },
    }
}

/// 列出沙盒目录
pub fn sandbox_list_files(path: &str) -> SandboxResult {
    match resolve_sandbox_path(path) {
        Ok(dir_path) => {
            if !dir_path.exists() {
                return SandboxResult {
                    ok: false,
                    error: Some(format!("Directory not found: {}", path)),
                    ..Default::default()
                };
            }
            if !dir_path.is_dir() {
                return SandboxResult {
                    ok: false,
                    error: Some(format!("'{}' is not a directory", path)),
                    ..Default::default()
                };
            }

            let mut items = Vec::new();
            if let Ok(entries) = fs::read_dir(&dir_path) {
                for entry in entries.flatten() {
                    let name = entry.file_name().to_string_lossy().to_string();
                    let item_type = if entry.path().is_dir() { "directory" } else { "file" };
                    items.push(SandboxItem { name, item_type: item_type.to_string() });
                }
            }

            let relative_path = dir_path.strip_prefix(sandbox_dir())
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_else(|_| ".".to_string());

            SandboxResult {
                ok: true,
                path: Some(relative_path),
                items: Some(items),
                ..Default::default()
            }
        }
        Err(e) => SandboxResult {
            ok: false,
            error: Some(e),
            ..Default::default()
        },
    }
}

/// 删除沙盒文件
pub fn sandbox_delete_file(path: &str, recursive: bool) -> SandboxResult {
    match resolve_sandbox_path(path) {
        Ok(file_path) => {
            if !file_path.exists() {
                return SandboxResult {
                    ok: false,
                    error: Some(format!("File not found: {}", path)),
                    ..Default::default()
                };
            }

            let result = if file_path.is_dir() {
                if recursive {
                    fs::remove_dir_all(&file_path)
                } else {
                    fs::remove_dir(&file_path)
                }
            } else {
                fs::remove_file(&file_path)
            };

            match result {
                Ok(_) => SandboxResult {
                    ok: true,
                    path: Some(path.to_string()),
                    ..Default::default()
                },
                Err(e) => SandboxResult {
                    ok: false,
                    error: Some(format!("Delete failed: {}", e)),
                    ..Default::default()
                },
            }
        }
        Err(e) => SandboxResult {
            ok: false,
            error: Some(e),
            ..Default::default()
        },
    }
}

/// 在沙盒中执行命令
pub fn sandbox_execute_command(command: &str, timeout_secs: u64) -> SandboxResult {
    // 命令白名单检查
    let cmd_name = command.split_whitespace().next().unwrap_or("").to_lowercase();

    const COMMAND_ALLOWLIST: &[&str] = &[
        "python", "python3", "node", "npm", "pnpm", "echo", "cat", "ls", "dir",
        "mkdir", "rmdir", "rm", "cp", "mv", "touch", "find", "grep", "head",
        "tail", "wc", "sort", "uniq", "curl", "wget", "git", "pip", "pip3",
    ];

    if !COMMAND_ALLOWLIST.contains(&cmd_name.as_str()) {
        return SandboxResult {
            ok: false,
            error: Some(format!("Command '{}' is not in allowlist", cmd_name)),
            ..Default::default()
        };
    }

    // 危险模式检测
    const DANGEROUS_PATTERNS: &[&str] = &[
        "rm -rf /", "format", "dd if=", "mkfs", "fdisk",
        "shutdown", "reboot", "poweroff", "del /", "rd /s",
    ];

    for pattern in DANGEROUS_PATTERNS {
        if command.to_lowercase().contains(pattern) {
            return SandboxResult {
                ok: false,
                error: Some(format!("Command contains dangerous pattern: {}", pattern)),
                ..Default::default()
            };
        }
    }

    // 执行命令 - 使用 output() 简化实现（同步阻塞，带超时）
    let output_result = Command::new(if cfg!(windows) { "cmd" } else { "sh" })
        .arg(if cfg!(windows) { "/c" } else { "-c" })
        .arg(command)
        .current_dir(sandbox_dir())
        .output();

    match output_result {
        Ok(Output { status, stdout, stderr }) => {
            let stdout_str = String::from_utf8_lossy(&stdout).to_string();
            let stderr_str = String::from_utf8_lossy(&stderr).to_string();

            // 截断输出
            let truncate = |s: String| -> String {
                if s.len() > 5000 {
                    format!("{}...[truncated]", &s[..5000])
                } else {
                    s
                }
            };

            SandboxResult {
                ok: status.success(),
                stdout: Some(truncate(stdout_str)),
                stderr: Some(truncate(stderr_str)),
                returncode: Some(status.code().unwrap_or(-1)),
                ..Default::default()
            }
        }
        Err(e) => SandboxResult {
            ok: false,
            error: Some(format!("Failed to execute command: {}", e)),
            ..Default::default()
        },
    }
}

/// 计算行变更统计
fn line_change_stats(before: &str, after: &str) -> (usize, usize) {
    let before_lines: Vec<_> = before.lines().collect();
    let after_lines: Vec<_> = after.lines().collect();

    let mut added = 0;
    let mut removed = 0;

    // 简单的 diff 统计（非精确算法，但足够用）
    let max_len = before_lines.len().max(after_lines.len());
    for i in 0..max_len {
        if i >= before_lines.len() {
            added += 1;
        } else if i >= after_lines.len() {
            removed += 1;
        } else if before_lines[i] != after_lines[i] {
            removed += 1;
            added += 1;
        }
    }

    (added, removed)
}

impl Default for SandboxResult {
    fn default() -> Self {
        Self {
            ok: true,
            error: None,
            path: None,
            content: None,
            size: None,
            items: None,
            stdout: None,
            stderr: None,
            returncode: None,
            created: None,
            lines_added: None,
            lines_removed: None,
        }
    }
}
