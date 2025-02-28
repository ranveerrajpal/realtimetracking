from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import pandas as pd
import os

app = FastAPI()

# Mount static files (for JavaScript & CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allowed Floor
ALLOWED_FLOOR = 1
csv_file = "data.csv"

# Ensure CSV file exists
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["Unique ID", "Name", "Floor", "Room No"])
    df.to_csv(csv_file, index=False)

# Load HTML file (Ensure `index.html` exists in the root)
html_file_path = "templates/index.html"
if not os.path.exists(html_file_path):
    raise FileNotFoundError(f"{html_file_path} not found!")

with open(html_file_path, "r") as file:
    html_content = file.read()

@app.get("/")
async def home():
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive data
            data = await websocket.receive_text()
            user_data = json.loads(data)

            # Extract details
            unique_id = user_data.get("uniqueID", "N/A")
            name = user_data.get("userName", "Unknown")
            room_no = user_data.get("room", "N/A")
            floor = user_data.get("floor", 0)
            status = user_data.get("status", 0)

            # Store data in CSV
            new_data = pd.DataFrame([[unique_id, name, floor, room_no]], 
                                    columns=["Unique ID", "Name", "Floor", "Room No"])
            new_data.to_csv(csv_file, mode='a', header=False, index=False)

            # Check for unauthorized floor access
            alert_status = floor > ALLOWED_FLOOR
            user_data["alert"] = alert_status

            # Send response back to client
            await websocket.send_json(user_data)

    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
