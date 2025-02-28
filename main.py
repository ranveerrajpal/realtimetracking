from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import datetime

app = FastAPI()

# ✅ Initialize an empty DataFrame
df = pd.DataFrame(columns=["uniqueID", "userName", "room", "floor", "status", "entry_time", "exit_time"])

# ✅ Route to Submit Data
@app.post("/submit-data")
async def submit_data(data: dict):
    """ Accepts JSON & stores worker entry/exit times in a DataFrame """
    global df  # Access the DataFrame globally

    try:
        uniqueID = data.get("uniqueID")
        userName = data.get("userName")
        room = data.get("room")
        floor = data.get("floor")
        status = data.get("status")  # "Enter" or "Exit"
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Validate required fields
        if None in [uniqueID, userName, room, floor, status]:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Check if the worker already has an entry
        existing_entry = df[(df["uniqueID"] == uniqueID) & (df["exit_time"].isna())]

        if status.lower() == "enter":
            if existing_entry.empty:
                # Add new entry with entry time
                new_entry = pd.DataFrame([[uniqueID, userName, room, floor, status, current_time, ""]], 
                                         columns=df.columns)
                df = pd.concat([df, new_entry], ignore_index=True)

        elif status.lower() == "exit":
            if not existing_entry.empty:
                # Update the latest entry with exit time
                df.loc[df["uniqueID"] == uniqueID, "exit_time"] = current_time

        return {"message": f"Worker {status} recorded successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Retrieve Labour Data for Display
@app.get("/get-labour-data")
async def get_labour_data():
    """ Fetch all worker tracking data from DataFrame """
    global df  # Access the DataFrame globally
    if df.empty:
        return {"message": "No data available"}
    
    return {"labour_records": df.to_dict(orient="records")}

# ✅ Serve HTML Page
@app.get("/")
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Labour Tracking System</title>
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                function fetchAndUpdate() {
                    fetch("/get-labour-data")
                        .then(response => response.json())
                        .then(data => {
                            let tableBody = document.getElementById("tableBody");
                            tableBody.innerHTML = ""; // Clear previous entries
                            if (data.labour_records) {
                                data.labour_records.forEach(entry => {
                                    let row = `<tr>
                                        <td>${entry.uniqueID}</td>
                                        <td>${entry.userName}</td>
                                        <td>${entry.room}</td>
                                        <td>${entry.floor}</td>
                                        <td>${entry.status}</td>
                                        <td>${entry.entry_time ? entry.entry_time : 'Pending'}</td>
                                        <td>${entry.exit_time ? entry.exit_time : 'Still Inside'}</td>
                                    </tr>`;
                                    tableBody.innerHTML += row;
                                });
                            }
                        })
                        .catch(err => console.error("Error fetching data:", err));
                }

                setInterval(fetchAndUpdate, 2000);
            });
        </script>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }
            th {
                background-color: lightgray;
            }
        </style>
    </head>
    <body>
        <h1>Labour Tracking System</h1>
        <table>
            <thead>
                <tr>
                    <th>Worker ID</th>
                    <th>Name</th>
                    <th>Room</th>
                    <th>Floor</th>
                    <th>Status</th>
                    <th>Entry Time</th>
                    <th>Exit Time</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                <tr><td colspan="7">Waiting for data...</td></tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
