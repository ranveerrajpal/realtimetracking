from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import time

app = FastAPI()

# ✅ Store active WebSocket connections
active_connections = set()

# ✅ Store worker positions & movement history
worker_positions = {}
worker_timeline = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ Handles WebSocket connections from Android App & Web Clients """
    await websocket.accept()
    active_connections.add(websocket)
    print("✅ WebSocket connection established.")

    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)

            uniqueID = json_data.get("uniqueID")
            userName = json_data.get("userName")
            room = json_data.get("room")
            floor = json_data.get("floor")
            status = json_data.get("status")  # ✅ Include Status

            # ✅ Check last known position
            last_room = worker_positions.get(uniqueID, {}).get("room")
            last_floor = worker_positions.get(uniqueID, {}).get("floor")

            worker_positions[uniqueID] = {"room": room, "floor": floor, "status": status}

            # ✅ Track movement in timeline
            if (last_room, last_floor) != (room, floor):  # Movement detected
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                if uniqueID not in worker_timeline:
                    worker_timeline[uniqueID] = []
                worker_timeline[uniqueID].append(f"{timestamp}: {userName} {status} {room} (Floor {floor})")

            # ✅ Unauthorized Entry Alert
            alert = None
            if floor == 2:  # Worker entered unauthorized floor
                alert = f"⚠️ ALERT: {userName} entered an unauthorized area!"

            # ✅ Send data to all clients
            for connection in active_connections:
                await connection.send_text(json.dumps({
                    "uniqueID": uniqueID,
                    "userName": userName,
                    "room": room,
                    "floor": floor,
                    "status": status,  # ✅ Include Status in WebSocket Broadcast
                    "timeline": worker_timeline.get(uniqueID, []),
                    "alert": alert
                }))

    except WebSocketDisconnect:
        print("⚠️ Client disconnected")
        active_connections.remove(websocket)

# ✅ Allow Android to Send Data via HTTP (Instead of WebSockets)
@app.post("/submit-data")
async def submit_data(data: dict):
    """ Receives JSON data and sends it to all WebSocket clients """
    json_data = json.dumps(data)  # Convert to JSON

    # ✅ Store worker location persistently
    uniqueID = data.get("uniqueID")
    userName = data.get("userName")
    room = data.get("room")
    floor = data.get("floor")
    status = data.get("status")  # ✅ Include Status

    last_room = worker_positions.get(uniqueID, {}).get("room")
    last_floor = worker_positions.get(uniqueID, {}).get("floor")

    worker_positions[uniqueID] = {"room": room, "floor": floor, "status": status}

    # ✅ Track movement in timeline
    if (last_room, last_floor) != (room, floor):  # Movement detected
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if uniqueID not in worker_timeline:
            worker_timeline[uniqueID] = []
        worker_timeline[uniqueID].append(f"{timestamp}: {userName} {status} {room} (Floor {floor})")

    # ✅ Unauthorized Entry Alert
    alert = None
    if floor == 2:  # Worker entered unauthorized floor
        alert = f"⚠️ ALERT: {userName} entered an unauthorized area!"

    # ✅ Send data to all clients
    for connection in active_connections:
        await connection.send_text(json.dumps({
            "uniqueID": uniqueID,
            "userName": userName,
            "room": room,
            "floor": floor,
            "status": status,  # ✅ Include Status in HTTP Broadcast
            "timeline": worker_timeline.get(uniqueID, []),
            "alert": alert
        }))

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

                let workerPositions = {};
                const tableBody = document.getElementById("tableBody");
                const timelineDiv = document.getElementById("timeline");
                const alertDiv = document.getElementById("alert");
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

                    // ✅ Draw Yellow Dots for Active Workers
                    for (const [workerID, location] of Object.entries(workerPositions)) {
                        if (location.room === "Room 1" && location.floor == 1) {
                            ctx.fillStyle = "yellow";
                            ctx.beginPath();
                            ctx.arc(125, 175, 10, 0, 2 * Math.PI);
                            ctx.fill();
                        }
                        if (location.room === "Room 2" && location.floor == 1) {
                            ctx.fillStyle = "yellow";
                            ctx.beginPath();
                            ctx.arc(325, 175, 10, 0, 2 * Math.PI);
                            ctx.fill();
                        }
                    }
                }

                ws.onmessage = function(event) {
                    let data = JSON.parse(event.data);
                    console.log("📩 Data Received:", data);

                    workerPositions[data.uniqueID] = { room: data.room, floor: data.floor, status: data.status };

                    drawRooms();

                    // ✅ Update Timeline
                    timelineDiv.innerHTML = "<h2>Worker Timeline</h2>";
                    if (data.timeline.length > 0) {
                        data.timeline.forEach(entry => {
                            timelineDiv.innerHTML += `<p>${entry}</p>`;
                        });
                    }

                    // ✅ Show Alert if Unauthorized Entry
                    if (data.alert) {
                        alertDiv.innerHTML = `<h2 style='color: red;'>${data.alert}</h2>`;
                    } else {
                        alertDiv.innerHTML = "";
                    }

                    // ✅ Show Worker Details in Table
                    let entryKey = `${data.uniqueID}-${data.userName}-${data.room}-${data.floor}-${data.status}`;
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
                        tableBody.innerHTML = row + tableBody.innerHTML;
                    }
                };
            });
        </script>
    </head>
    <body>
        <h1>Live Room Tracking</h1>
        <div id="alert"></div>
        <canvas id="floorCanvas" width="500" height="400"></canvas>
        <div id="timeline"></div>
        <table><tbody id="tableBody"></tbody></table>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
