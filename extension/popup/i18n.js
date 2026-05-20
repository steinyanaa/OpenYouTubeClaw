(() => {
  const STORAGE_KEY = "openyoutubeclaw.uiLanguage";
  const DEFAULT_LANGUAGE = "zh-CN";

  const zhToEn = {
    "YouTube Content Lens": "YouTube Content Lens",
    "未连接": "Offline",
    "首页先放一边，这里是你最近更可能点开的。": "Skip the homepage. These are the videos you are more likely to open next.",
    "推荐": "For You",
    "我的画像": "Profile",
    "聊聊你的想法": "Chat",
    "For You": "For You",
    "这几条，你大概会点开": "Videos you will probably open",
    "换一批": "Refresh",
    "当前可换": "Available",
    "最近补进": "Recently added",
    "现在在忙": "Working on",
    "还没刷出新东西": "No new recommendations yet",
    "稍等一下，新的推荐马上来。": "Wait a moment while new recommendations are prepared.",
    "Profile": "Profile",
    "我感觉你大概是这样的": "Here is what your profile looks like",
    "不是光看你点过啥，我主要在看你会为哪种东西停下来。": "It is based on what makes you pause, not only what you clicked.",
    "画像还没攒起来": "Your profile is not ready yet",
    "先跑一遍 openyoutubeclaw init，再回来看看。": "Run openyoutubeclaw init first, then come back here.",
    "这会儿的你": "Current portrait",
    "核心特质": "Core traits",
    "深层需求": "Deep needs",
    "价值偏好": "Values",
    "内在驱动力": "Motivational drivers",
    "感兴趣的方向": "Interests",
    "明显会避开": "Avoids",
    "常看的频道": "Favorite channels",
    "大致处在什么阶段": "Life stage",
    "这阵子更像在经历什么": "Current phase",
    "认知风格": "Cognitive style",
    "内容口味": "Content taste",
    "使用场景": "Usage context",
    "探索开放度": "Exploration openness",
    "猜测兴趣": "Speculative interests",
    "Agent 最近新记住了什么": "What the agent recently learned",
    "加载更多": "Load more",
    "当前活跃的洞察": "Active insights",
    "近期观察到的": "Recent observations",
    "写点你的想法和口味": "Share your thoughts and taste",
    "发出去": "Send",
    "消息": "Messages",
    "后端设置": "Backend settings",
    "模型": "Models",
    "平台源": "Sources",
    "调度": "Scheduler",
    "通用": "General",
    "日志": "Logs",
    "LLM 模型": "LLM models",
    "默认 Provider": "Default provider",
    "认证方式": "Auth mode",
    "YouTube 搜索 query 预算": "YouTube search query budget",
    "YouTube 热门候选预算": "YouTube trending candidate budget",
    "YouTube 订阅频道预算": "YouTube channel budget",
    "YouTube 请求间隔秒数": "YouTube request interval seconds",
    "YouTube 没有独立插件 producer；这些值会限制 yt_search / yt_trending / yt_channel 三个 discovery 策略的单轮规模。": "YouTube discovery uses yt_search, yt_trending, and yt_channel; these values limit each round.",
    "候选池来源占比": "Candidate pool source share",
    "候选池 YouTube 占比": "YouTube pool share",
    "按已有信号建议比例": "Suggest from existing signals",
    "后端地址": "Backend host",
    "后端端口": "Backend port",
    "保存配置": "Save settings",
    "更多": "More",
    "语言": "Language",
    "Agent 这会儿先替你盯着。": "The agent is keeping an eye on things for you."
  };

  const placeholderZhToEn = {
    "说说你最近怎么想——你是什么样的人、怎么想、喜欢什么、讨厌什么，为什么会停下来，都可以直接说。": "Tell the agent what you are thinking, what you like or dislike, and what makes you stop scrolling.",
    "留空使用默认": "Leave blank to use default",
    "留空继承 provider 默认模型": "Leave blank to inherit the provider model"
  };

  const attrZhToEn = {
    "设置": "Settings",
    "打开设置": "Open settings",
    "消息": "Messages",
    "查看消息": "View messages",
    "返回": "Back",
    "关闭消息": "Close messages",
    "关闭设置": "Close settings"
  };

  function reverseMap(map) {
    return Object.fromEntries(Object.entries(map).map(([key, value]) => [value, key]));
  }

  function mapFor(language, baseMap) {
    return language === "en-US" ? baseMap : reverseMap(baseMap);
  }

  function normalize(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function translateTextNodes(root, language) {
    const map = mapFor(language, zhToEn);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const value = normalize(node.nodeValue);
        if (!value || !map[value]) return NodeFilter.FILTER_REJECT;
        const parent = node.parentElement;
        if (parent && ["SCRIPT", "STYLE", "TEXTAREA", "OPTION"].includes(parent.tagName)) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const original = normalize(node.nodeValue);
      node.nodeValue = node.nodeValue.replace(original, map[original]);
    }
  }

  function translateAttributes(root, language) {
    const placeholderMap = mapFor(language, placeholderZhToEn);
    const attrMap = mapFor(language, attrZhToEn);
    for (const element of root.querySelectorAll("[placeholder]")) {
      const value = element.getAttribute("placeholder");
      if (placeholderMap[value]) element.setAttribute("placeholder", placeholderMap[value]);
    }
    for (const attr of ["title", "aria-label"]) {
      for (const element of root.querySelectorAll(`[${attr}]`)) {
        const value = element.getAttribute(attr);
        if (attrMap[value]) element.setAttribute(attr, attrMap[value]);
      }
    }
  }

  function applyLanguage(language) {
    document.documentElement.lang = language;
    translateTextNodes(document.body, language);
    translateAttributes(document.body, language);
    const selector = document.getElementById("languageSelect");
    if (selector) selector.value = language;
    try {
      localStorage.setItem(STORAGE_KEY, language);
    } catch (_) {
      // localStorage can be unavailable in restricted browser contexts.
    }
  }

  function initialLanguage() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "zh-CN" || saved === "en-US") return saved;
    } catch (_) {
      // Ignore storage errors.
    }
    return (navigator.language || "").toLowerCase().startsWith("zh") ? DEFAULT_LANGUAGE : "en-US";
  }

  document.addEventListener("DOMContentLoaded", () => {
    const selector = document.getElementById("languageSelect");
    if (selector) selector.addEventListener("change", () => applyLanguage(selector.value));
    applyLanguage(initialLanguage());
  });
})();
