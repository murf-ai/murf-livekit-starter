import sqlite3
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Raksha Live Analytics</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: #f0f2f5; margin: 0; padding: 40px; text-align: center; }
        h1 { color: #1a1a1a; margin-bottom: 10px; }
        p { color: #666; margin-bottom: 40px; }
        .grid { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }
        .card { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); width: 220px; text-align: center; border: 1px solid #e1e4e8; }
        .card h3 { margin: 0 0 15px 0; color: #4a5568; font-size: 16px; text-transform: uppercase; letter-spacing: 1px; }
        .number { font-size: 56px; font-weight: 800; margin: 0; }
        .total { color: #2b6cb0; }
        .success { color: #38a169; }
        .failed { color: #e53e3e; }
        .description { font-size: 13px; color: #a0aec0; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Raksha Command Center</h1>
    <p>Live Dashboard: Tracking outbound and inbound emergency triage calls.</p>
    
    <div class="grid">
        <div class="card">
            <h3>Total Calls</h3>
            <p class="number total" id="total">-</p>
            <p class="description">All attempted sessions</p>
        </div>
        <div class="card">
            <h3>Successful Calls</h3>
            <p class="number success" id="success">-</p>
            <p class="description">Triage saved or help dispatched</p>
        </div>
        <div class="card">
            <h3>Failed Calls</h3>
            <p class="number failed" id="failed">-</p>
            <p class="description">Hang-ups or opt-outs</p>
        </div>
    </div>

    <script>
        async function updateDashboard() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                document.getElementById('total').innerText = data.total;
                document.getElementById('success').innerText = data.success;
                document.getElementById('failed').innerText = data.failed;
            } catch (error) {
                console.error("Error fetching stats:", error);
            }
        }
        
        // Auto-refresh the dashboard every 2 seconds
        setInterval(updateDashboard, 2000);
        updateDashboard();
    </script>
</body>
</html>
"""

class AnalyticsServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/stats':
            try:
                conn = sqlite3.connect("raksha_triage.db")
                c = conn.cursor()
                
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_logs'")
                if not c.fetchone():
                    stats = {"total": 0, "success": 0, "failed": 0}
                else:
                    c.execute("SELECT count(*) FROM call_logs")
                    total = c.fetchone()[0]
                    c.execute("SELECT count(*) FROM call_logs WHERE status = 'SUCCESS'")
                    success = c.fetchone()[0]
                    c.execute("SELECT count(*) FROM call_logs WHERE status = 'FAILED'")
                    failed = c.fetchone()[0]
                    stats = {"total": total, "success": success, "failed": failed}
                conn.close()
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(stats).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    # Suppress server logs in the terminal to keep it clean
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = 8000
    httpd = HTTPServer(('', port), AnalyticsServer)
    print(f"🚀 Raksha Dashboard is LIVE at: http://localhost:{port}")
    print("Keep this terminal open. Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()