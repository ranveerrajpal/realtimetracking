from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
    df = pd.DataFrame(columns=["Unique ID", "Name", "Longitude", "Latitude", "Floor"])
    df.to_csv(csv_file, index=False)

# Load HTML
with open("templates/index.html", "r") as file:
    html_content = file.read()

@app.get("/")
async def home():
    return HTMLResponse(html_content)

# WebSocket Endpoint (Fix)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # Accept connection
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

@app.post("/submit-data")
async def submit_data(uniqueID: str, userName: str, room: str, floor: int, status: str):
    try:
        # Append the data to the CSV file
        new_data = pd.DataFrame([[uniqueID, userName, room, floor, status]], 
                                 columns=["uniqueID", "userName", "room", "floor", "status"])
        new_data.to_csv(csv_file, mode='a', header=False, index=False)
        
        return {"message": "Data received successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get-csv")
async def get_csv():
    if os.path.exists(csv_file):
        return FileResponse(csv_file, media_type='text/csv', filename='data.csv')
    else:
        raise HTTPException(status_code=404, detail="CSV file not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
