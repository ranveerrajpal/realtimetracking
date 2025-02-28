from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CSV File
csv_file = "data.csv"

# Ensure CSV file exists
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["uniqueID", "userName", "room", "floor", "status"])
    df.to_csv(csv_file, index=False)

# Store active WebSocket connections
active_connections = set()

@app.get("/")
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Real-Time Room Tracking</title>
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                const canvas = document.getElementById("floorCanvas");
                const ctx = canvas.getContext("2d");

                const rooms = {
                    "Room 1": { x: 125, y: 275 },
                    "Room 2": { x: 325, y: 275 },
                    "Room 3": { x: 125, y: 125 },
                    "Room 4": { x: 325, y: 125 }
                };

                function drawFloorPlan() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.fillStyle = "lightgray";
                    ctx.strokeStyle = "red";
                    ctx.lineWidth = 2;

                    ctx.fillRect(50, 200, 150, 150);
                    ctx.strokeRect(50, 200, 150, 150);

                    ctx.fillRect(250, 200, 150, 150);
                    ctx.strokeRect(250, 200, 150, 150);

                    ctx.fillRect(50, 50, 150, 150);
                    ctx.strokeRect(50, 50, 150, 150);

                    ctx.fillRect(250, 50, 150, 150);
                    ctx.strokeRect(250, 50, 150, 150);

                    ctx.fillStyle = "black";
                    ctx.font = "16px Arial";
                    ctx.fillText("Room 1", 100, 275);
                    ctx.fillText("Room 2", 300, 275);
                    ctx.fillText("Room 3", 100, 125);
                    ctx.fillText("Room 4", 300, 125);
                }

                async function fetchAndUpdate() {
                    try {
                        const response = await fetch("/latest-positions");
                        const data = await response.json();

                        if (data.positions) {
                            drawFloorPlan();

                            data.positions.forEach((entry) => {
                                if (rooms[entry.room]) {
                                    ctx.fillStyle = "blue";
                                    ctx.beginPath();
                                    ctx.arc(rooms[entry.room].x, rooms[entry.room].y, 10, 0, 2 * Math.PI);
                                    ctx.fill();
                                    console.log(`✅ Dot placed in ${entry.room} at (${rooms[entry.room].x}, ${rooms[entry.room].y})`);
                                }
                            });
                        }
                    } catch (error) {
                        console.error("Error fetching positions:", error);
                    }
                }

                setInterval(fetchAndUpdate, 2000);
                drawFloorPlan();
            });
        </script>
    </head>
    <body>
        <h1>Real-Time Room Tracking</h1>
        <canvas id="floorCanvas" width="500" height="500"></canvas>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

# WebSocket Endpoint (Broadcasts received data to all clients)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print("✅ WebSocket connection established.")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)

                required_fields = ["uniqueID", "userName", "room", "floor", "status"]
                if not all(field in json_data for field in required_fields):
                    await websocket.send_text(json.dumps({"error": "Missing required fields"}))
                    continue

                new_data = pd.DataFrame([[json_data["uniqueID"], json_data["userName"], json_data["room"], json_data["floor"], json_data["status"]]], 
                                        columns=required_fields)
                new_data.to_csv(csv_file, mode='a', header=False, index=False)

                for connection in active_connections:
                    await connection.send_text(json.dumps(json_data))

                print(f"📩 Data received & broadcasted: {json_data}")

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))

    except WebSocketDisconnect:
        print("⚠️ Client disconnected")
        active_connections.remove(websocket)

# ✅ HTTP POST API Endpoint (Submit Data)
@app.post("/submit-data")
async def submit_data(data: dict):
    """ Accepts JSON & stores data in CSV """
    try:
        # Extract fields from JSON payload
        uniqueID = data.get("uniqueID")
        userName = data.get("userName")
        room = data.get("room")
        floor = data.get("floor")
        status = data.get("status")

        # Validate fields
        if None in [uniqueID, userName, room, floor, status]:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Append data to CSV
        new_data = pd.DataFrame([[uniqueID, userName, room, floor, status]], 
                                 columns=["uniqueID", "userName", "room", "floor", "status"])
        new_data.to_csv(csv_file, mode='a', header=False, index=False)

        return {"message": "Data received successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/latest-positions")
async def get_latest_positions():
    """ Read the latest room positions from the CSV file. """
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)

        if df.empty:
            return {"message": "No tracking data available"}

        latest_positions = df.groupby("uniqueID").last().reset_index()
        positions = latest_positions.to_dict(orient="records")

        return {"positions": positions}
    
    else:
        raise HTTPException(status_code=404, detail="CSV file not found")

@app.get("/get-csv")
async def get_csv():
    if os.path.exists(csv_file):
        return FileResponse(csv_file, media_type="text/csv", filename="data.csv")
    else:
        raise HTTPException(status_code=404, detail="CSV file not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
