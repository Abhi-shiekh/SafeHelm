from flask import Flask, jsonify, render_template_string
import serial
import threading
import json
import time

app = Flask(__name__)

SERIAL_PORT = "COM5"
BAUD_RATE   = 115200

latest_data = {
    "ir": 0, "accel": 0.0,
    "helmet_on": False, "impact": False,
    "timestamp": 0, "connected": False
}

def read_serial():
    global latest_data
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            print(f"[Serial] Connected on {SERIAL_PORT}")
            while True:
                line = ser.readline().decode("utf-8").strip()
                if not line.startswith("{"):
                    continue
                data = json.loads(line)
                print(f"[ESP32] {line}")
                latest_data = {
                    "ir":        data.get("ir", 0),
                    "accel":     data.get("accel", 0.0),
                    "helmet_on": data.get("helmet_on", False),
                    "impact":    data.get("impact", False),
                    "timestamp": time.time(),
                    "connected": True
                }
        except serial.SerialException as e:
            print(f"[Serial] Port error: {e} — retrying in 3s")
            latest_data["connected"] = False
            time.sleep(3)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"[Serial] Unexpected error: {e}")
            time.sleep(1)

t = threading.Thread(target=read_serial, daemon=True)
t.start()

@app.route('/api/data')
def get_data():
    global latest_data
    if time.time() - latest_data.get("timestamp", 0) > 3:
        latest_data["connected"] = False
    return jsonify(latest_data)

@app.route('/')
def dashboard():
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SafeHelm Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      color: #e2e8f0;
      min-height: 100vh;
      padding: 20px;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 32px;
      padding: 20px 24px;
      background: rgba(30, 41, 59, 0.6);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 16px;
    }
    .logo {
      font-size: 32px;
      font-weight: 800;
      background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .site-info { font-size: 13px; color: #94a3b8; line-height: 1.5; }
    .connection-status {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(15, 23, 42, 0.5);
      border-radius: 24px;
      font-size: 12px;
      font-weight: 600;
    }
    .status-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: #10b981;
      animation: pulse 2s ease-in-out infinite;
    }
    .status-dot.disconnected { background: #ef4444; animation: none; }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.6; transform: scale(1.1); }
    }
    .time { font-size: 12px; color: #64748b; margin-top: 4px; text-align: right; }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
      margin-bottom: 24px;
    }
    .card {
      background: rgba(30, 41, 59, 0.4);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 16px;
      padding: 28px;
      transition: all 0.3s ease;
    }
    .card:hover { border-color: rgba(148, 163, 184, 0.2); transform: translateY(-2px); }
    .card-title {
      font-size: 12px; font-weight: 700;
      color: #94a3b8; text-transform: uppercase;
      letter-spacing: 1.5px; margin-bottom: 20px;
    }
    .status-display {
      font-size: 48px; font-weight: 800;
      padding: 32px; border-radius: 12px;
      text-align: center; margin-bottom: 20px;
      transition: all 0.4s ease; letter-spacing: -1px;
    }
    .status-on   { background: linear-gradient(135deg, #10b981, #059669); color: white; box-shadow: 0 8px 24px rgba(16,185,129,0.3); }
    .status-off  { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; box-shadow: 0 8px 24px rgba(239,68,68,0.3); animation: alertPulse 1s ease-in-out infinite; }
    .status-safe { background: linear-gradient(135deg, #10b981, #059669); color: white; box-shadow: 0 8px 24px rgba(16,185,129,0.3); }
    .status-impact { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; box-shadow: 0 8px 24px rgba(245,158,11,0.4); animation: alertPulse 0.8s ease-in-out infinite; }
    @keyframes alertPulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.02); }
    }
    .readings { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .reading {
      background: rgba(15, 23, 42, 0.6);
      padding: 16px; border-radius: 8px;
      border-left: 3px solid #3b82f6;
    }
    .reading-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .reading-value { font-size: 24px; font-weight: 700; color: #e2e8f0; }
    .worker-card {
      grid-column: span 2;
      background: rgba(30, 41, 59, 0.4);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(148, 163, 184, 0.1);
      border-radius: 16px; padding: 28px;
    }
    .worker-info { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
    .info-item { background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 8px; }
    .info-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .info-value { font-size: 18px; font-weight: 600; color: #e2e8f0; }
    .no-connection { text-align: center; padding: 60px 20px; color: #64748b; }
    .no-connection-icon { font-size: 64px; margin-bottom: 16px; opacity: 0.5; }
    .no-connection-text { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
    .no-connection-hint { font-size: 13px; color: #475569; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div style="display:flex;align-items:center;gap:16px;">
        <div class="logo">SafeHelm</div>
        <div class="site-info">
          Bengaluru Metro — Phase 3<br>
          <span style="color:#64748b;">Real-time worker safety monitoring</span>
        </div>
      </div>
      <div>
        <div class="connection-status">
          <div class="status-dot" id="conn-dot"></div>
          <span id="conn-text">Connecting...</span>
        </div>
        <div class="time" id="clock"></div>
      </div>
    </div>

    <div class="grid" id="main-grid">
      <div class="card">
        <div class="card-title">Helmet Status</div>
        <div class="status-display status-on" id="helmet">HELMET ON</div>
        <div class="readings">
          <div class="reading"><div class="reading-label">IR Sensor Value</div><div class="reading-value" id="ir-val">0</div></div>
          <div class="reading"><div class="reading-label">Detection Threshold</div><div class="reading-value">2000</div></div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Impact Detection</div>
        <div class="status-display status-safe" id="impact">SAFE</div>
        <div class="readings">
          <div class="reading"><div class="reading-label">Acceleration</div><div class="reading-value" id="accel-val">0.0 g</div></div>
          <div class="reading"><div class="reading-label">Impact Threshold</div><div class="reading-value">2.5 g</div></div>
        </div>
      </div>
      <div class="worker-card">
        <div class="card-title">Worker Information</div>
        <div class="worker-info">
          <div class="info-item"><div class="info-label">Worker ID</div><div class="info-value">W-001</div></div>
          <div class="info-item"><div class="info-label">Shift Time</div><div class="info-value">09:00 - 18:00</div></div>
          <div class="info-item"><div class="info-label">Last Update</div><div class="info-value" id="last-update">--:--:--</div></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function pad(n) { return n.toString().padStart(2,'0'); }
    function nowStr() {
      const d = new Date();
      return pad(d.getHours())+':'+pad(d.getMinutes())+':'+pad(d.getSeconds());
    }
    setInterval(() => document.getElementById('clock').textContent = nowStr(), 1000);

    const originalGrid = document.getElementById('main-grid').innerHTML;

    function updateDashboard() {
      fetch('/api/data').then(r => r.json()).then(data => {
        const dot      = document.getElementById('conn-dot');
        const connText = document.getElementById('conn-text');

        if (!data.connected) {
          dot.classList.add('disconnected');
          connText.textContent = 'No Connection';
          document.getElementById('main-grid').innerHTML = `
            <div style="grid-column:span 2;">
              <div class="no-connection">
                <div class="no-connection-icon">⚠</div>
                <div class="no-connection-text">ESP32 Not Connected</div>
                <div class="no-connection-hint">Check USB cable and close Arduino Serial Monitor</div>
              </div>
            </div>`;
          return;
        }

        if (!document.getElementById('helmet')) {
          document.getElementById('main-grid').innerHTML = originalGrid;
        }

        dot.classList.remove('disconnected');
        connText.textContent = 'Connected via USB';

        const helmetEl = document.getElementById('helmet');
        helmetEl.textContent = data.helmet_on ? 'HELMET ON' : 'HELMET OFF';
        helmetEl.className   = data.helmet_on ? 'status-display status-on' : 'status-display status-off';

        const impactEl = document.getElementById('impact');
        impactEl.textContent = data.impact ? 'IMPACT!' : 'SAFE';
        impactEl.className   = data.impact ? 'status-display status-impact' : 'status-display status-safe';

        document.getElementById('ir-val').textContent    = data.ir;
        document.getElementById('accel-val').textContent = data.accel.toFixed(2) + ' g';
        document.getElementById('last-update').textContent = nowStr();
      }).catch(console.error);
    }

    updateDashboard();
    setInterval(updateDashboard, 500);
  </script>
</body>
</html>''')

if __name__ == '__main__':
    print(f"[SafeHelm] Reading from {SERIAL_PORT} at {BAUD_RATE} baud")
    print(f"[SafeHelm] Dashboard → http://localhost:5000")
    print(f"[SafeHelm] Make sure Arduino Serial Monitor is CLOSED")
    app.run(debug=False, port=5000, host='0.0.0.0')