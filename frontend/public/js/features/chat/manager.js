import EventBus from "../../core/event-bus.js";

export class ChatManager {
  constructor({ connection, historyManager }) {
    this.connection = connection;
    this.messageQueue = [];
    this.currentMessagePart = null;
    this.isProcessing = false;
    this.isWaitingForResponse = false;
    this.historyManager = historyManager;
    this.setupSocketHandlers();
    this.setupEventListeners();
  }

  setupSocketHandlers() {
    this.connection.onmessage((event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "reply") {
          if (data.isMultiPart) {
            this.handleMultiPartMessage(data);
          } else {
            this.handleSingleMessage(data);
          }
        }
      } catch (e) {
        console.error("消息解析错误:", e, "原始数据:", event.data);
        EventBus.emit("chat:error", { error: e, rawData: event.data });
      }
    });
  }

  setupEventListeners() {
    EventBus.on("ui:send-message", (text) => {
      this.sendOrContinue(text);
    });

    EventBus.on("ui:continue", () => {
      this.handleContinue();
    });

    EventBus.on("chat:enable-input", () => {
      this.enableInput();
    });
  }

  handleMultiPartMessage(data) {
    this.messageQueue.push(data);

    if (data.partIndex === 0 && !this.isProcessing) {
      this.processNextMessage();
    }
  }

  handleSingleMessage(data) {
    console.log("【处理单条消息】", data);
    EventBus.emit("chat:message", {
      content: data.message || data.content,
      emotion: data.emotion,
      audioFile: data.audioFile,
      isFinal: true,
    });
  }

  processNextMessage() {
    if (this.messageQueue.length === 0) {
      this.isProcessing = false;
      return;
    }

    this.isProcessing = true;
    this.currentMessagePart = this.messageQueue.shift();
    this.historyManager.addMessage(
      null,
      this.currentMessagePart.message,
      this.currentMessagePart.partIndex ===
        this.currentMessagePart.totalParts - 1
    );

    EventBus.emit("chat:message", {
      content: this.currentMessagePart.message,
      emotion: this.currentMessagePart.emotion,
      originalTag: this.currentMessagePart.originalTag,
      audioFile: this.currentMessagePart.audioFile,
      isFinal:
        this.currentMessagePart.partIndex ===
        this.currentMessagePart.totalParts - 1,
      motionText: this.currentMessagePart.motionText,
    });
  }

  sendOrContinue(text) {
    if (this.isProcessing) {
      this.handleContinue();
    } else if (text) {
      this.sendMessage(text);
    }
  }

  sendMessage(text) {
    if (!text.trim()) return;

    const message = {
      type: "message",
      content: text,
    };

    this.connection.send(message);
    this.historyManager.addMessage(text, null, false);

    // 更新状态
    this.isWaitingForResponse = true;
    this.messageQueue = [];
    this.isProcessing = false;

    EventBus.emit("chat:message-sent", message);
    EventBus.emit("chat:thinking", true);
  }

  handleContinue() {
    // 检查是否是最后一条消息
    if (
      this.currentMessagePart &&
      this.currentMessagePart.partIndex ===
        this.currentMessagePart.totalParts - 1
    ) {
      this.resetConversationState();
      EventBus.emit("chat:conversation-end");
    } else {
      this.processNextMessage();
    }
  }

  enableInput() {
    this.isWaitingForResponse = false;
    EventBus.emit("chat:input-enabled");
  }

  resetConversationState() {
    this.currentMessagePart = null;
    this.messageQueue = [];
    this.isProcessing = false;
    this.isWaitingForResponse = false;

    EventBus.emit("chat:reset");
    EventBus.emit("chat:enable-input");
  }
}
