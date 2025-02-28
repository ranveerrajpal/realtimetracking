from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import pandas as pd
import os

app = FastAPI()

# Mount static files for JavaScript & CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allowed Floor
ALLOWED_FLOOR = 1
csv_file = "data.csv"

# Ensure CSV exists
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["Unique ID", "Name", "Floor", "Room No"])
    df.to_csv(csv_file, index=False)

# Load HTML
with open("templates/index.html", "r") as file:
    html_content = file.read()

@app.get("/")
async def home():
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            user_data = json.loads(data)

            # Extract details
            unique_id = user_data["unique_id"]
            name = user_data["name"]
            floor = user_data["floor"]
            room_no = user_data["room_no"]

            # Store in CSV
            new_data = pd.DataFrame([[unique_id, name, floor, room_no]], 
                                    columns=["Unique ID", "Name", "Floor", "Room No"])
            new_data.to_csv(csv_file, mode='a', header=False, index=False)

            # Alert if unauthorized floor
            user_data["alert"] = floor > ALLOWED_FLOOR

            # Send updated data
            await websocket.send_json(user_data)

    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
