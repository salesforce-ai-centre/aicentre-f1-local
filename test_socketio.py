"""Quick test to verify Flask-SocketIO is serving the client library"""
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>SocketIO Test</title></head>
    <body>
        <h1>Socket.IO Test</h1>
        <div id="status">Connecting...</div>
        <script src="/socket.io/socket.io.js"></script>
        <script>
            const socket = io();
            socket.on('connect', () => {
                document.getElementById('status').textContent = 'Connected!';
                console.log('Socket.IO connected');
            });
            socket.on('disconnect', () => {
                document.getElementById('status').textContent = 'Disconnected';
                console.log('Socket.IO disconnected');
            });
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting test server on http://localhost:5000")
    print("Socket.IO client should be served at http://localhost:5000/socket.io/socket.io.js")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
