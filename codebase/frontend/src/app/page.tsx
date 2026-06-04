"use client";

import React, { useState, useEffect, useRef } from "react";

// API Base URL (FastAPI)
const API_BASE = "http://localhost:8000";

// Interfaces to match Python SessionState
interface UserPreference {
  food_style: string | null;
  place_type: string | null;
  experience: string | null;
  nightlife: boolean;
  budget: string | null;
  arrival_date_str: string | null;
  arrival_day_of_week: string | null;
  num_days: number;
  onboarding_step: number;
}

interface ChatMessage {
  role: string;
  content: string;
}

interface SessionState {
  preference: UserPreference;
  chat_history: ChatMessage[];
  itinerary_generated: boolean;
}

interface ClosedPlace {
  id: number;
  name: string;
  district: string;
  category: string;
}

// Translations dictionaries
const foodLabels: Record<string, string> = {
  street_food: "Đường phố",
  restaurant: "Nhà hàng",
  hidden_gem: "Local hidden gem",
  mixed: "Kết hợp",
};

const placeLabels: Record<string, string> = {
  culture_history: "Văn hóa & lịch sử",
  shopping_entertainment: "Vui chơi & mua sắm",
  chill_cafe: "Chill & cafe",
  mixed: "Tất cả",
};

const expLabels: Record<string, string> = {
  local: "Local",
  tourist: "Tourist-friendly",
  family: "Gia đình",
};

const budgetLabels: Record<string, string> = {
  low: "Tiết kiệm (< 500k)",
  medium: "Vừa phải (500k–1tr)",
  high: "Thoải mái (> 1tr)",
};

const dayLabels: Record<string, string> = {
  Monday: "Thứ 2",
  Tuesday: "Thứ 3",
  Wednesday: "Thứ 4",
  Thursday: "Thứ 5",
  Friday: "Thứ 6",
  Saturday: "Thứ 7",
  Sunday: "Chủ nhật",
};

// Markdown to HTML helper
function markdownToHtml(text: string): string {
  if (!text) return "";
  
  // Escape basic HTML tags to avoid breaking markup but retain text
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Convert Markdown Links: [text](url)
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #0f172a; text-decoration: underline; font-weight: 500;">$1</a>');
  
  // Convert Bold: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Convert Italics: _(text)_ and _text_
  html = html.replace(/_\((.*?)\)_/g, "<em>$1</em>");
  html = html.replace(/_(.*?)_/g, "<em>$1</em>");
  
  // Convert list items
  const lines = html.split("\n");
  let inList = false;
  const newLines = [];
  
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("•") || stripped.startsWith("- ") || stripped.startsWith("* ")) {
      let contentPart = stripped.substring(1).trim();
      if (stripped.startsWith("- ") || stripped.startsWith("* ")) {
        contentPart = stripped.substring(2).trim();
      }
      
      if (!inList) {
        newLines.push('<ul style="margin: 6px 0 10px 20px; padding-left: 0; list-style-type: disc;">');
        inList = true;
      }
      newLines.push(`<li style="margin-bottom: 4px; color: #1e293b;">${contentPart}</li>`);
    } else {
      if (inList) {
        newLines.push("</ul>");
        inList = false;
      }
      newLines.push(line);
    }
  }
  
  if (inList) {
    newLines.push("</ul>");
  }
  
  html = newLines.join("\n");
  html = html.replace(/\n/g, "<br>");
  
  // Spacing cleanups
  html = html.replace(/<\/ul><br>/g, "</ul>");
  html = html.replace(/<br><ul>/g, "<ul>");
  html = html.replace(/<br><li>/g, "<li>");
  html = html.replace(/<\/li><br>/g, "</li>");
  html = html.replace(/<ul><br>/g, "<ul>");
  
  return html;
}

export default function Home() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [closedPlaces, setClosedPlaces] = useState<ClosedPlace[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to chat bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.chat_history, loading]);

  // Initial load
  useEffect(() => {
    initApp();
  }, []);

  // Auto-focus input when loading finishes or session loads
  useEffect(() => {
    if (!loading && session) {
      inputRef.current?.focus();
    }
  }, [loading, session]);

  // Fetch closed places when day of week changes
  useEffect(() => {
    if (session?.preference.arrival_day_of_week) {
      fetchClosedPlaces(session.preference.arrival_day_of_week);
    } else {
      setClosedPlaces([]);
    }
  }, [session?.preference.arrival_day_of_week]);

  const initApp = async () => {
    setLoading(true);
    setConnectionError(null);
    try {
      const res = await fetch(`${API_BASE}/api/start`, { method: "POST" });
      if (!res.ok) throw new Error("Could not start API session");
      const data = await res.json();
      setSession(data.session);
    } catch (err: any) {
      console.error(err);
      setConnectionError("Không thể kết nối đến server API Python (localhost:8000). Hãy chắc chắn backend đang chạy.");
    } finally {
      setLoading(false);
    }
  };

  const fetchClosedPlaces = async (day: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/closed-places?day=${day}`);
      if (res.ok) {
        const data = await res.json();
        setClosedPlaces(data.places || []);
      }
    } catch (err) {
      console.error("Error loading closed places", err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const messageText = inputValue.trim();
    if (!messageText || !session || loading) return;

    // Clear input immediately
    setInputValue("");
    setLoading(true);

    // Optimistically update frontend UI chat history with user message
    const updatedHistory = [...session.chat_history, { role: "user", content: messageText }];
    setSession({
      ...session,
      chat_history: updatedHistory,
    });

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: messageText,
          session: session, // Send the original session state
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      setSession(data.session);
    } catch (err: any) {
      console.error(err);
      // Append connection error message
      setSession({
        ...session,
        chat_history: [
          ...updatedHistory,
          {
            role: "assistant",
            content: "Có lỗi xảy ra khi kết nối đến AI. Vui lòng kiểm tra cổng backend hoặc khóa API.",
          },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    if (confirm("Bạn có chắc muốn làm mới toàn bộ cuộc trò chuyện?")) {
      initApp();
    }
  };

  const getPrefDisplay = (key: keyof UserPreference, labels: Record<string, string>) => {
    if (!session) return "chưa chọn";
    const value = session.preference[key];
    if (value === null || value === undefined) return "chưa chọn";
    
    // special handling for nightlife in experience
    if (key === "experience") {
      const expVal = labels[value as string] || String(value);
      return session.preference.nightlife ? `${expVal} + Nightlife` : expVal;
    }

    if (typeof value === "string") {
      return labels[value.replace("_", " ")] || labels[value] || value;
    }
    return String(value);
  };

  const isPrefDone = (key: keyof UserPreference) => {
    if (!session) return false;
    return session.preference[key] !== null && session.preference[key] !== undefined;
  };

  return (
    <div className="app-container">
      {/* Sidebar (Left) */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-title">HaNoi Guide</h2>
          <p className="sidebar-caption">AI Travel Agent · 179 địa điểm thực</p>
        </div>
        
        <div className="divider"></div>
        
        {/* Weather Display */}
        <div style={{ padding: "12px 16px", backgroundColor: "#f0f9ff", borderRadius: "8px", marginBottom: "16px" }}>
          <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#0369a1", fontWeight: 600 }}>Thời tiết Hà Nội hôm nay</h4>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "28px" }}>☀️</span>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 600, color: "#1e293b" }}>28°C</div>
              <div style={{ fontSize: "12px", color: "#64748b" }}>Nắng, ẩm độ 65%</div>
            </div>
          </div>
          <div style={{ marginTop: "8px", fontSize: "12px", color: "#64748b" }}>
            💧 Khả năng mưa: 20%
          </div>
        </div>
        
        <h4 className="sidebar-section-title">Sở thích của bạn</h4>
        <div className="pref-cards-container">
          <div className={`pref-card ${isPrefDone("food_style") ? "done" : "pending"}`}>
            <span className="pref-card-label">Ăn uống</span>
            <span className="pref-card-value">
              {getPrefDisplay("food_style", foodLabels)}
            </span>
          </div>

          <div className={`pref-card ${isPrefDone("place_type") ? "done" : "pending"}`}>
            <span className="pref-card-label">Tham quan</span>
            <span className="pref-card-value">
              {getPrefDisplay("place_type", placeLabels)}
            </span>
          </div>

          <div className={`pref-card ${isPrefDone("experience") ? "done" : "pending"}`}>
            <span className="pref-card-label">Phong cách</span>
            <span className="pref-card-value">
              {getPrefDisplay("experience", expLabels)}
            </span>
          </div>

          <div className={`pref-card ${isPrefDone("budget") ? "done" : "pending"}`}>
            <span className="pref-card-label">Ngân sách</span>
            <span className="pref-card-value">
              {getPrefDisplay("budget", budgetLabels)}
            </span>
          </div>

          <div className={`pref-card ${isPrefDone("arrival_day_of_week") ? "done" : "pending"}`}>
            <span className="pref-card-label">Ngày đến</span>
            <span className="pref-card-value">
              {getPrefDisplay("arrival_day_of_week", dayLabels)}
            </span>
          </div>
        </div>

        {/* Closed Places Warnings */}
        {closedPlaces.length > 0 && (
          <>
            <div className="divider"></div>
            <h4 className="sidebar-section-title">Địa điểm đóng cửa</h4>
            <div className="warn-list">
              {closedPlaces.map((place) => (
                <div className="warn-card" key={place.id}>
                  <div className="warn-card-title">{place.name}</div>
                  <div className="warn-card-detail">
                    {place.district} - đóng cửa {dayLabels[session?.preference.arrival_day_of_week || ""]}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        <button className="reset-button" onClick={handleReset}>
          Bắt đầu lại
        </button>
      </aside>

      {/* Main chat area (Right) */}
      <main className="chat-area">
        <header className="chat-header">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <img src="/robot.jpg" alt="HaNoi Guide" style={{ width: "40px", height: "40px", borderRadius: "50%", objectFit: "cover" }} />
            <h1 className="chat-header-title">HaNoi Guide</h1>
          </div>
          <p className="chat-header-subtitle">
            Chatbot AI tạo lịch trình du lịch Hà Nội cá nhân hóa — tham quan + ăn uống + nightlife
          </p>
        </header>

        {connectionError && (
          <div style={{ padding: "16px 32px", backgroundColor: "#fef2f2", color: "#991b1b", fontSize: "14px", borderBottom: "1px solid #fee2e2" }}>
            {connectionError}
          </div>
        )}

        {/* Message Stream */}
        <div className="messages-container">
          {session?.chat_history.map((msg, index) => {
            const isAssistant = msg.role === "assistant" || msg.role === "model";
            return (
              <div
                className={`chat-msg-row ${isAssistant ? "assistant" : "user"}`}
                key={index}
              >
                <div className={`avatar ${isAssistant ? "assistant" : "user"}`}>
                  {isAssistant ? "H" : "U"}
                </div>
                <div
                  className="bubble"
                  dangerouslySetInnerHTML={{ __html: markdownToHtml(msg.content) }}
                />
              </div>
            );
          })}
          
          {loading && (
            <div className="chat-msg-row assistant">
              <div className="avatar assistant">H</div>
              <div className="bubble" style={{ display: "flex", alignItems: "center", gap: "8px", backgroundColor: "#f1f5f9" }}>
                <div className="dot-pulse" style={{ width: "8px", height: "8px", margin: 0 }}></div>
                <span style={{ color: "#64748b", fontStyle: "italic" }}>Bot đang suy nghĩ... chờ nhé 💭</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat input box */}
        <form className="input-container" onSubmit={handleSendMessage}>
          <div className="input-box-wrapper">
            <input
              ref={inputRef}
              type="text"
              className="input-field"
              placeholder="Nhắn tin cho HaNoi Guide..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={loading || !session}
            />
          </div>
          <button
            type="submit"
            className="send-button"
            disabled={!inputValue.trim() || loading || !session}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </main>
    </div>
  );
}
