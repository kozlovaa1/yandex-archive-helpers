from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        print(f"RECEIVED {content_length} bytes")
        
        try:
            # Try to decode form data if it starts with data=
            decoded = body.decode('utf-8')
            if decoded.startswith('data='):
                import urllib.parse
                # Remove data= and unquote
                # Using unquote_plus to handle '+' as spaces
                json_str = urllib.parse.unquote_plus(decoded[5:])
                # Save clean JSON
                with open("received_data.json", "w", encoding='utf-8') as f:
                    f.write(json_str)
            else:
                # Assume raw
                with open("received_data.json", "wb") as f:
                    f.write(body)
        except Exception as e:
            print(f"Error decoding: {e}")
            # Save raw just in case
            with open("received_data_raw.bin", "wb") as f:
                f.write(body)
            
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        # Read file back to count items? No, just acknowledge receipt.
        # The processing happens async in watcher.py, so server doesn't know filtered count immediately.
        # But we can at least confirm we got valid JSON.
        response = {"status": "ok", "message": "Data received and queued for processing."}
        try:
             # Basic validation check
             if 'json_str' in locals():
                 data = json.loads(json_str)
                 response['received_items'] = len(data)
        except:
             response['status'] = "warning"
             response['message'] = "Data received but format uncertain."

        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    port = 8080
    print(f"Starting server on {port}...")
    httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
