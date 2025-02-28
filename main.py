from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import os
import time

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# CSV File
csv_file = "data.csv"

# Ensure CSV file exists
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["uniqueID", "userName", "room", "floor", "status"])
    df.to_csv(csv_file, index=False)

# ✅ Route to Submit Data
@app.post("/submit-data")
async def submit_data(data: dict):
    """ Accepts JSON & stores data in CSV """
    try:
        uniqueID = data.get("uniqueID")
        userName = data.get("userName")
        room = data.get("room")
        floor = data.get("floor")
        status = data.get("status")

        # Validate required fields
        if None in [uniqueID, userName, room, floor, status]:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Append data to CSV
        new_data = pd.DataFrame([[uniqueID, userName, room, floor, status]], 
                                 columns=["uniqueID", "userName", "room", "floor", "status"])
        new_data.to_csv(csv_file, mode='a', header=False, index=False)

        return {"message": "Data received successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Retrieve CSV Data for Animation
@app.get("/get-csv-data")
async def get_csv_data():
    """ Fetch all CSV entries for animation """
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        if df.empty:
            return {"message": "No tracking data available"}
        return {"positions": df.to_dict(orient="records")}
    else:
        raise HTTPException(status_code=404, detail="CSV file not found")

# ✅ Serve HTML Page
@app.get("/")
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Animated Tracking</title>
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

                let currentPosition = { x: 125, y: 275 }; // Default start position

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

                function animateDot(targetX, targetY) {
                    let dx = (targetX - currentPosition.x) / 10;
                    let dy = (targetY - currentPosition.y) / 10;
                    let steps = 10;
                    
                    function moveStep() {
                        if (steps > 0) {
                            currentPosition.x += dx;
                            currentPosition.y += dy;
                            steps--;
                            drawFloorPlan();
                            ctx.fillStyle = "blue";
                            ctx.beginPath();
                            ctx.arc(currentPosition.x, currentPosition.y, 10, 0, 2 * Math.PI);
                            ctx.fill();
                            requestAnimationFrame(moveStep);
                        }
                    }
                    moveStep();
                }

                function fetchAndUpdate() {
                    fetch("/get-csv-data")
                        .then(response => response.json())
                        .then(data => {
                            if (data.positions && data.positions.length > 0) {
                                let lastEntry = data.positions[data.positions.length - 1];
                                if (rooms[lastEntry.room]) {
                                    animateDot(rooms[lastEntry.room].x, rooms[lastEntry.room].y);
                                }
                            }
                        })
                        .catch(err => console.error("Error fetching positions:", err));
                }

                setInterval(fetchAndUpdate, 2000);
                drawFloorPlan();
            });
        </script>
    </head>
    <body>
        <h1>Animated Real-Time Room Tracking</h1>
        <canvas id="floorCanvas" width="500" height="500"></canvas>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
