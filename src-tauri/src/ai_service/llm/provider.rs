use anyhow::Result;
use async_trait::async_trait;
use futures_util;
use reqwest::Client;
use serde::Serialize;

use crate::ai_service::llm::{ChunkStream, LlmChunk};
use crate::ai_service::types::{LlmMessage, ToolCall, ToolDefinition};

/// `complete_with_tools` 的返回值。
#[derive(Debug, Clone, Serialize)]
pub struct LlmModelInfo {
    pub id: String,
    pub display_name: Option<String>,
    pub context_length: Option<u64>,
    pub supports_reasoning: bool,
    pub supports_thinking_type: Option<String>,
}

#[derive(Debug, Clone)]
pub struct LlmResponseWithTools {
    /// 文本回复（可能为空，如果 LLM 只返回 tool call）。
    pub content: Option<String>,
    /// LLM 请求调用的工具列表。
    pub tool_calls: Option<Vec<ToolCall>>,
}

/// LLM 供应商协议：不同供应商的唯一区别在于 HTTP 请求/响应的格式。
///
/// 对标 Python `BaseLLMProvider` ABC。
/// 参照 `TtsAdapter` trait 使用 `async_trait` + `Send + Sync` 的模式。
#[async_trait]
pub trait LlmProvider: Send + Sync {
    async fn list_models(&self, _http: &Client) -> Result<Vec<LlmModelInfo>> {
        Ok(Vec::new())
    }

    /// 非流式：发送消息列表，返回完整回复文本。
    async fn complete(&self, http: &Client, messages: &[LlmMessage]) -> Result<String>;

    /// 流式：返回逐字符（或逐 token）的 chunk 流，每个 chunk 区分内容与思考链。
    async fn complete_stream(&self, http: &Client, messages: &[LlmMessage]) -> Result<ChunkStream>;

    /// 非流式 + function calling。
    ///
    /// 默认实现 fallback 到 `complete()`（不支持 tools 的供应商）。
    async fn complete_with_tools(
        &self,
        http: &Client,
        messages: &[LlmMessage],
        _tools: &[ToolDefinition],
        _tool_choice: Option<&str>,
    ) -> Result<LlmResponseWithTools> {
        let text = self.complete(http, messages).await?;
        Ok(LlmResponseWithTools {
            content: Some(text),
            tool_calls: None,
        })
    }

    /// 流式 + function calling。
    ///
    /// 在流式过程中检测工具调用，返回工具事件流。
    /// 当检测到工具调用时，流会暂停并返回工具调用信息，等待外部执行后继续。
    async fn complete_stream_with_tools(
        &self,
        http: &Client,
        messages: &[LlmMessage],
        tools: &[ToolDefinition],
        tool_choice: Option<&str>,
    ) -> Result<ChunkStream> {
        // 默认实现 fallback：直接使用 non-streaming version
        let response = self.complete_with_tools(http, messages, tools, tool_choice).await?;

        // 如果有工具调用，转换为 ToolCall chunk
        if let Some(calls) = response.tool_calls {
            let stream = futures_util::stream::iter(
                calls
                    .into_iter()
                    .map(|tc| Ok(LlmChunk::ToolCall(tc)))
                    .collect::<Vec<_>>()
            );
            return Ok(Box::pin(stream));
        }

        // 如果是文本回复，转换为 Content chunk
        if let Some(content) = response.content {
            return Ok(Box::pin(futures_util::stream::iter(vec![Ok(LlmChunk::Content(content))])));
        }

        // 空响应
        Ok(Box::pin(futures_util::stream::empty()))
    }
}
