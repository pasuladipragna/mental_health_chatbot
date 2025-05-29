// static/js/bundle.js

// === DARK MODE TOGGLE ===
document.getElementById("dark-mode-toggle")?.addEventListener("click", () => {
  document.body.classList.toggle("dark");
  localStorage.setItem("darkMode", document.body.classList.contains("dark") ? "enabled" : "disabled");
});
window.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("darkMode") === "enabled") {
    document.body.classList.add("dark");
  }
});

// === TYPING INDICATOR ===
function showTypingIndicator() {
  const botMessage = document.createElement("div");
  botMessage.className = "bot message";
  botMessage.innerHTML = '<span class="typing-indicator"><span>.</span><span>.</span><span>.</span></span>';
  document.getElementById("chat-box")?.appendChild(botMessage);
  scrollToBottom();
  return botMessage;
}
function scrollToBottom() {
  const chatBox = document.getElementById("chat-box");
  if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

// === SUGGESTED REPLIES ===
function addSuggestedReplies(tips = []) {
  const container = document.getElementById("suggested-replies");
  if (!container) return;
  container.innerHTML = '';
  tips.forEach(tip => {
    const btn = document.createElement("button");
    btn.textContent = tip;
    btn.onclick = () => sendMessage(tip);
    container.appendChild(btn);
  });
}

// === EXPORT FEATURES ===
function exportChatJSON(chatHistory) {
  const blob = new Blob([JSON.stringify(chatHistory, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "chat_history.json";
  link.click();
}
function exportChatCSV(chatHistory) {
  const rows = [["Timestamp", "Sender", "Message"]];
  chatHistory.forEach(chat => rows.push([chat.timestamp, chat.sender, chat.message]));
  const csv = rows.map(row => row.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "chat_history.csv";
  link.click();
}
function printChat() {
  window.print();
}

// === TOAST NOTIFICATIONS ===
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// === MOOD TRENDS CHART ===
function loadMoodChart(moodData) {
  const ctx = document.getElementById("moodChart")?.getContext("2d");
  if (!ctx) return;
  new Chart(ctx, {
    type: "line",
    data: {
      labels: moodData.timestamps,
      datasets: [{
        label: "Mood Trend",
        data: moodData.values,
        fill: false,
        borderColor: "#8e44ad",
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } }
    }
  });
}

// === VOICE INPUT (Web Speech API) ===
function startVoiceInput() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    sendMessage(transcript);
  };

  recognition.onerror = function(event) {
    showToast("Voice input error: " + event.error, "error");
  };

  recognition.start();
}

// === LOADING ANIMATION (optional overlay spinner) ===
function showLoadingOverlay() {
  const overlay = document.createElement("div");
  overlay.className = "loading-overlay";
  overlay.innerHTML = '<div class="spinner"></div>';
  document.body.appendChild(overlay);
}
function hideLoadingOverlay() {
  document.querySelector(".loading-overlay")?.remove();
}

function speakBotMessage(message) {
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = 'en-US';
    utterance.pitch = 1;
    utterance.rate = 1;
    utterance.volume = 1;
    speechSynthesis.speak(utterance);
}
