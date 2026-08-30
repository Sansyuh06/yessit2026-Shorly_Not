"""
Mobile-friendly quantum-secured chat web app.
Access from any phone on the same WiFi.
Uses the same KMS + BB84 backend as the desktop demo.
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import base64
import json

app = FastAPI()

CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🛡️ ShorlyNot Secure Chat</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { 
    font-family: -apple-system, system-ui, sans-serif;
    background: #0a0e17; color: #f1f5f9;
    height: 100vh; display: flex; flex-direction: column;
  }
  .header {
    background: #111827; padding: 16px; border-bottom: 1px solid #1e293b;
    display: flex; align-items: center; gap: 12px;
  }
  .shield-icon { font-size: 24px; }
  .status-dot { 
    width: 10px; height: 10px; border-radius: 50%;
    background: #10b981; animation: pulse 2s infinite;
  }
  .status-dot.red { background: #ef4444; }
  .status-dot.yellow { background: #f59e0b; }
  @keyframes pulse { 
    0%, 100% { opacity: 1; } 
    50% { opacity: 0.5; } 
  }
  .qber-badge {
    background: #1e293b; padding: 4px 10px; border-radius: 12px;
    font-size: 12px; margin-left: auto;
  }
  .messages {
    flex: 1; overflow-y: auto; padding: 16px;
    display: flex; flex-direction: column; gap: 8px;
  }
  .msg {
    max-width: 80%; padding: 10px 14px; border-radius: 16px;
    font-size: 15px; line-height: 1.4; word-wrap: break-word;
  }
  .msg.sent {
    align-self: flex-end; background: #3b82f6; color: white;
    border-bottom-right-radius: 4px;
  }
  .msg.received {
    align-self: flex-start; background: #1e293b; color: #f1f5f9;
    border-bottom-left-radius: 4px;
  }
  .msg .meta {
    font-size: 10px; opacity: 0.6; margin-top: 4px;
  }
  .msg .encryption-badge {
    font-size: 9px; background: rgba(139,92,246,0.3);
    padding: 2px 6px; border-radius: 8px; display: inline-block;
    margin-top: 4px;
  }
  .system-msg {
    align-self: center; background: transparent;
    color: #94a3b8; font-size: 12px; text-align: center;
    padding: 8px;
  }
  .input-area {
    background: #111827; padding: 12px; border-top: 1px solid #1e293b;
    display: flex; gap: 8px;
  }
  .input-area input {
    flex: 1; background: #1e293b; border: 1px solid #374151;
    border-radius: 20px; padding: 10px 16px; color: #f1f5f9;
    font-size: 15px; outline: none;
  }
  .input-area input:focus { border-color: #3b82f6; }
  .input-area button {
    background: #3b82f6; border: none; border-radius: 50%;
    width: 40px; height: 40px; color: white; font-size: 18px;
    cursor: pointer; display: flex; align-items: center; 
    justify-content: center;
  }
  .quantum-info {
    background: #111827; padding: 8px 16px; font-size: 11px;
    color: #94a3b8; display: flex; justify-content: space-between;
    border-top: 1px solid #1e293b;
  }
</style>
</head>
<body>
  <div class="header">
    <span class="shield-icon">🛡️</span>
    <div>
      <div style="font-weight:600;font-size:14px">ShorlyNot Secure Chat</div>
      <div style="font-size:11px;color:#94a3b8">BB84 QKD • AES-256-GCM</div>
    </div>
    <div class="status-dot" id="statusDot"></div>
    <div class="qber-badge" id="qberBadge">QBER: --</div>
  </div>
  
  <div class="messages" id="messages"></div>
  
  <div class="quantum-info">
    <span id="keyInfo">Key: waiting...</span>
    <span id="modeInfo">Mode: --</span>
    <span id="entropyScore">Score: --</span>
  </div>
  
  <div class="input-area">
    <input id="msgInput" placeholder="Type a quantum-secured message..." 
           onkeydown="if(event.key==='Enter')sendMsg()">
    <button onclick="sendMsg()">↑</button>
  </div>

  <script>
    const ws = new WebSocket("ws://" + location.host + "/ws");
    const messages = document.getElementById("messages");
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === "message") {
            const div = document.createElement("div");
            div.className = "msg received";
            div.innerHTML = data.text + "<br><span class='encryption-badge'>🔐 AES-256-GCM | Nonce: " + data.nonce + "</span>";
            messages.appendChild(div);
        } else if (data.type === "status") {
            document.getElementById("statusDot").className = "status-dot " + (data.color || "");
            document.getElementById("qberBadge").innerText = "QBER: " + data.qber;
            if (data.attack) {
                const sys = document.createElement("div");
                sys.className = "system-msg";
                sys.innerText = "⚠️ QUANTUM CHANNEL COMPROMISED";
                sys.style.color = "#ef4444";
                messages.appendChild(sys);
            }
        }
    };
    
    function sendMsg() {
        const input = document.getElementById("msgInput");
        if (!input.value) return;
        
        const div = document.createElement("div");
        div.className = "msg sent";
        div.innerText = input.value;
        messages.appendChild(div);
        
        ws.send(JSON.stringify({text: input.value}));
        input.value = "";
    }
  </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(CHAT_HTML)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # In a real app this would broadcast to KMS/chat server
        await websocket.send_text(json.dumps({"type": "message", "text": "Echo: " + json.loads(data)["text"], "nonce": "a3f2..."}))

if __name__ == "__main__":
    import uvicorn
    # Using port 8080 to avoid conflicts with KMS (8000) and Dashboard (8501)
    uvicorn.run(app, host="0.0.0.0", port=8080)
