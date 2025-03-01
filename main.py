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

            # ✅ Broadcast data to all connected web clients
            for connection in active_connections:
                await connection.send_text(data)

    except WebSocketDisconnect:
        print("⚠️ Client disconnected")
        active_connections.remove(websocket)

# ✅ Allow Android to Send Data via HTTP (Instead of WebSockets)
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
        <title>Live Room Tracking</title>
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                const ws = new WebSocket("wss://" + window.location.host + "/ws");

                // ✅ Canvas Setup
                const canvas = document.getElementById("floorCanvas");
                const ctx = canvas.getContext("2d");

                let room1Occupied = false;
                let room2Occupied = false;
                const tableBody = document.getElementById("tableBody");
                let receivedEntries = new Set();

                function drawRooms() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    // ✅ Draw Room 1
                    ctx.fillStyle = "lightgray";
                    ctx.fillRect(50, 100, 150, 150);
                    ctx.strokeStyle = "black";
                    ctx.strokeRect(50, 100, 150, 150);
                    ctx.fillStyle = "black";
                    ctx.fillText("Room 1", 100, 80);

                    // ✅ Draw Room 2 (180° opposite)
                    ctx.fillStyle = "lightgray";
                    ctx.fillRect(250, 100, 150, 150);
                    ctx.strokeStyle = "black";
                    ctx.strokeRect(250, 100, 150, 150);
                    ctx.fillStyle = "black";
                    ctx.fillText("Room 2", 300, 80);

                    // ✅ Draw Yellow Dot in Room 1 if occupied
                    if (room1Occupied) {
                        ctx.fillStyle = "yellow";
                        ctx.beginPath();
                        ctx.arc(125, 175, 10, 0, 2 * Math.PI);
                        ctx.fill();
                    }

                    // ✅ Draw Yellow Dot in Room 2 if occupied
                    if (room2Occupied) {
                        ctx.fillStyle = "yellow";
                        ctx.beginPath();
                        ctx.arc(325, 175, 10, 0, 2 * Math.PI);
                        ctx.fill();
                    }
                }

                ws.onmessage = function(event) {
                    let data = JSON.parse(event.data);
                    console.log("📩 Data Received:", data);

                    // ✅ Unique Key for Tracking
                    let entryKey = `${data.uniqueID}-${data.userName}-${data.room}-${data.floor}-${data.status}`;

                    // ✅ Update Yellow Dots Based on Room Data
                    if (data.room === "Room 1" && data.floor == 1) {
                        room1Occupied = true;
                        room2Occupied = false;
                    } 
                    else if (data.room === "Room 2" && data.floor == 1) {
                        room1Occupied = false;
                        room2Occupied = true;
                    } else {
                        room1Occupied = false;
                        room2Occupied = false;
                    }

                    drawRooms(); // ✅ Update Canvas

                    // ✅ Show Worker Details in Table
                    if (!receivedEntries.has(entryKey)) { 
                        receivedEntries.add(entryKey);
                        let row = `<tr>
                            <td>${data.uniqueID}</td>
                            <td>${data.userName}</td>
                            <td>${data.room}</td>
                            <td>${data.floor}</td>
                            <td>${data.status}</td>
                            <td>${new Date().toLocaleString()}</td>
                        </tr>`;
                        tableBody.innerHTML = row + tableBody.innerHTML; // Add new data at the top
                    }
                };

                ws.onclose = () => console.log("⚠️ WebSocket connection closed.");

                drawRooms(); // ✅ Initial Draw
            });
        </script>
        <style>
            canvas {
                border: 2px solid black;
                margin-top: 20px;
            }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid black; padding: 8px; text-align: center; }
            th { background-color: lightgray; }
        </style>
    </head>
    <body>
        <h1>Live Room Tracking</h1>
        <canvas id="floorCanvas" width="500" height="400"></canvas>
        <h2>Worker Entry Details</h2>
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
