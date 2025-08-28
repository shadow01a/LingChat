export type WebSocketHandler = (data: any) => void;

export interface WebSocketMessage {
  type: string;
  data: any;
}

export interface WebSocketChatMessage {
  type: string;
  emotion: string;
  originalTag: string;
  message: string;
  motionText: string;
  audioFile: string;
  originalMessage: string;
  isFinal: boolean;
}

export enum WebSocketMessageTypes {
  // 正常模式的消息类型
  MESSAGE = "message", // 用户发送的信息
  AIREPLY = "reply", // 来自AI的回复
  STATUS_UPDATE = "status_update", // 静态资源更新
  ERROR = "error",

  // 剧本模式下的消息类型
  SCRIPT_NARRATION = "script_narration", // 旁白
  SCRIPT_PLAYER = "script_player", // 玩家
  SCRIPT_DIALOGUE = "script_dialog", // 角色对话

  SCRIPT_BACKGROUND = "script_background", // 旁白
}
