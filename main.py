from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
import os

app = FastAPI()

# Mount static files for JavaScript & CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allowed Floor
ALLOWED_FLOOR = 1
csv_file = "data.csv"

# Ensure CSV file exists
if not os.path.exists(csv_file):
    df = pd.DataFrame(columns=["uniqueID", "userName", "room", "floor", "status"])
    df.to_csv(csv_file, index=False)

# Load HTML
with open("templates/index.html", "r") as file:
    html_content = file.read()

@app.get("/")
async def home():
    return HTMLResponse(html_content)

# WebSocket Endpoint (Now receives JSON properly)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # Accept WebSocket connection
    try:
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)  # Parse JSON

                # Extract required fields
                uniqueID = json_data.get("uniqueID")
                userName = json_data.get("userName")
                room = json_data.get("room")
                floor = json_data.get("floor")
                status = json_data.get("status")

                # Validate required fields
                if None in [uniqueID, userName, room, floor, status]:
                    await websocket.send_text(json.dumps({"error": "Missing required fields"}))
                    continue
                
                # Append data to CSV
                new_data = pd.DataFrame([[uniqueID, userName, room, floor, status]], 
                                        columns=["uniqueID", "userName", "room", "floor", "status"])
                new_data.to_csv(csv_file, mode='a', header=False, index=False)

                await websocket.send_text(json.dumps({"message": "Data saved successfully"}))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))

    except WebSocketDisconnect:
        print("Client disconnected")

# HTTP POST API Endpoint (Accepts JSON & stores data in CSV)
@app.post("/submit-data")
async def submit_data(data: dict):
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

# API to Get CSV File
@app.get("/get-csv")
async def get_csv():
    if os.path.exists(csv_file):
        return FileResponse(csv_file, media_type="text/csv", filename="data.csv")
    else:
        raise HTTPException(status_code=404, detail="CSV file not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
