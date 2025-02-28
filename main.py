from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# ✅ Store active WebSocket connections
active_connections = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ Handles WebSocket connections from both Android App & Web Clients """
    await websocket.accept()
    active_connections.add(websocket)
    print("✅ WebSocket connection established.")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Received Data: {data}")  # Debugging log

            # Broadcast data to all connected web clients
            for connection in active_connections:
                await connection.send_text(data)

    except WebSocketDisconnect:
        print("⚠️ Client disconnected")
        active_connections.remove(websocket)

# ✅ Optional: Allow Android to Send Data via HTTP (Instead of WebSockets)
@app.post("/submit-data")
async def submit_data(data: dict):
    """ Receives JSON data and sends it to all WebSocket clients """
    json_data = json.dumps(data)  # Convert to JSON

    # ✅ Send data to all connected WebSocket clients
    for connection in active_connections:
        await connection.send_text(json_data)

    return {"message": "Data sent to web clients"}

# ✅ Serve Web Page
@app.get("/")
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Labour Tracking</title>
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                const tableBody = document.getElementById("tableBody");
                const ws = new WebSocket("wss://" + window.location.host + "/ws");

                ws.onmessage = function(event) {
                    let data = JSON.parse(event.data);
                    let row = `<tr>
                        <td>${data.uniqueID}</td>
                        <td>${data.userName}</td>
                        <td>${data.room}</td>
                        <td>${data.floor}</td>
                        <td>${data.status}</td>
                        <td>${new Date().toLocaleString()}</td>
                    </tr>`;
                    tableBody.innerHTML = row + tableBody.innerHTML; // Add new data at the top
                };

                ws.onclose = () => console.log("⚠️ WebSocket connection closed.");
            });
        </script>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid black; padding: 8px; text-align: center; }
            th { background-color: lightgray; }
        </style>
    </head>
    <body>
        <h1>Live Labour Tracking</h1>
        <table>
            <thead>
                <tr>
                    <th>Worker ID</th>
                    <th>Name</th>
                    <th>Room</th>
                    <th>Floor</th>
                    <th>Status</th>
                    <th>Received Time</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                <tr><td colspan="6">Waiting for data...</td></tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
