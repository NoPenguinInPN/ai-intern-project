// js/chat.js - 带动态省略号加载动画的版本
document.addEventListener("DOMContentLoaded", () => {
  let isProcessing = false;
  const chatContainer = document.getElementById("chatContainer");
  const composer = document.getElementById("composer");
  const sendBtn = document.getElementById("sendBtn");

  // 事件监听
  sendBtn.addEventListener("click", sendMessage);
  composer.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // 处理粘贴事件，仅保留纯文本
  composer.addEventListener("paste", (e) => {
    e.preventDefault();
    const text = (e.clipboardData || window.clipboardData).getData("text/plain");
    document.execCommand("insertText", false, text);
  });

  // 启动加载动画：在 element 后面循环显示省略号模式，返回 interval ID
  function startLoadingAnimation(element) {
    const patterns = ['。', '。。', '。。。', '。。', '。', '']; // 循环模式
    let idx = 0;
    // 初始文本不带省略号或只带第一种
    element.textContent = '正在查询中 ';
    return setInterval(() => {
      element.textContent = '正在查询中' + patterns[idx];
      idx = (idx + 1) % patterns.length;
    }, 500);
  }

  // 发送消息到后端
  function sendMessage() {
    if (isProcessing) return;

    const text = composer.textContent.trim();
    if (!text) return;

    isProcessing = true;
    sendBtn.disabled = true;
    addChatMessage(text, "user");
    composer.innerHTML = "";

    // 添加 loading 消息并启动动画
    const loadingMessage = addChatMessage("正在查询中", "bot");
    const loadingInterval = startLoadingAnimation(loadingMessage);

    fetch("http://localhost:5001/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      clearInterval(loadingInterval);
      if (data.reply) {
        const replyText = data.reply.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
        loadingMessage.innerHTML = marked.parse(replyText || "");
      } else if (data.error) {
        loadingMessage.innerHTML = marked.parse(`后端错误: ${data.error}`);
      } else {
        loadingMessage.innerHTML = marked.parse("未知响应格式");
      }
    })
    .catch(error => {
      clearInterval(loadingInterval);
      console.error("请求失败:", error);
      loadingMessage.innerHTML = marked.parse(`请求失败: ${error.message}`);
    })
    .finally(() => {
      isProcessing = false;
      sendBtn.disabled = false;
    });
  }

  // 添加聊天消息到界面，返回该消息元素
  function addChatMessage(text, sender) {
    const bubble = document.createElement("div");
    bubble.className = `chat-message ${sender}`;
    if (sender === "bot") {
      bubble.innerHTML = marked.parse(text || "");
    } else {
      bubble.textContent = text;
    }
    bubble.style.alignSelf = sender === "user" ? "flex-end" : "flex-start";
    chatContainer.appendChild(bubble);
    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return bubble;
  }
});
