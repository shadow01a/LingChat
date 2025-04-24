// 统一DOM元素引用
export const DOM = {
  // 输入区域
  input: document.getElementById("inputMessage"),
  sendBtn: document.getElementById("sendButton"),

  // 状态显示
  status: document.getElementById("status"),
  audioStatus: document.getElementById("audioStatus"),

  // 头像区域
  avatar: {
    img: document.querySelector(".main-box img"),
    container: document.querySelector(".avatar-container"),
    title: document.getElementById("character"),
    subtitle: document.getElementById("character-sub"),
    emotion: document.getElementById("character-emotion"),
    bubble: document.querySelector(".bubble"),
  },

  // 音频
  audioPlayer: document.getElementById("audioPlayer"),
  bubbleAudio: document.getElementById("audioPlayerBubble"),
  effectAudio: document.getElementById("audioPlayerEffect"),

  // 特效背景
  canvas: document.getElementById("canvas"),
  fgEffect: document.getElementById("frontpage-effect"),

  // 菜单部分
  menuToggle: document.getElementById("menu-toggle"),
  menuContent: document.getElementById("menu-content"),
  closeMenu: document.getElementById("close-menu"),

  menuText: document.getElementById("menu-text"),
  textPage: document.getElementById("text-page"),

  menuImage: document.getElementById("menu-image"),
  imagePage: document.getElementById("background-page"),

  menuSound: document.getElementById("menu-sound"),
  soundPage: document.getElementById("sound-page"),

  // 文本部分
  text: {
    speedInput: document.getElementById("speed-option"),
    testMessage: document.getElementById("testmessage"),
  },

  // 菜单历史部分
  history: {
    toggle: document.getElementById("menu-history"),
    content: document.getElementById("history-page"),
    list: document.getElementById("history-list"),
    clearBtn: document.getElementById("clear-history"),
  },

  // 图像部分
  image: {
    // 预览部分
    qinling: document.getElementById("qinling"),
    qinlingtest: document.getElementById("qinlingtest"),
    filterKuosan: document.getElementById("filter-kuosan"),

    // 添加自定义背景功能
    uploadBgBtn: document.getElementById("upload-bg-btn"),
    uploadBgInput: document.getElementById("upload-bg-input"),
    uploadStatus: document.getElementById("upload-status"),
    bgOption: document.querySelectorAll(".bg-option"),
    bgOptions: document.querySelector(".bg-options"),

    kuosanPreview: document.getElementById("kuosan-preview"),
    kousanPreviewImg: document.getElementById("kuosan-preview-img"),
    kuosanTest: document.getElementById("kuosan-test"),
  },
};

// 安全元素访问
export const getSafeDOM = (key) => {
  const el = DOM[key];
  if (!el) console.log(`DOM元素未找到: ${key}`);
  return el;
};
