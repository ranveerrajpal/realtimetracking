document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("floorCanvas");
    const ctx = canvas.getContext("2d");

    if (!canvas || !ctx) {
        console.error("❌ Canvas element not found!");
        return;
    }

    console.log("🚀 Initializing 2D Map...");

    // Define room positions on the canvas (adjust as needed)
    const rooms = {
        "Room 1": { x: 125, y: 275 },  // Center of Room 1
        "Room 2": { x: 325, y: 275 },  // Center of Room 2
        "Room 3": { x: 125, y: 125 },  // Center of Room 3
        "Room 4": { x: 325, y: 125 }   // Center of Room 4
    };

    // WebSocket connection
    const socket = new WebSocket("wss://realtimetracking-zcq4.onrender.com/ws");

    socket.onopen = () => {
        console.log("✅ WebSocket connection established.");
    };

    socket.onmessage = (event) => {
        console.log("📩 Received Data:", event.data);
        try {
            const data = JSON.parse(event.data);
            if (data.room && rooms[data.room]) {
                console.log(`🚀 Updating dot for: ${data.room}`);
                update2DMap(data.room);
            } else {
                console.warn("⚠️ Room data missing or incorrect:", data);
            }
        } catch (error) {
            console.error("❌ Error parsing WebSocket message:", error);
        }
    };

    socket.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
    };

    socket.onclose = () => {
        console.log("⚠️ WebSocket connection closed.");
    };

    // Function to draw the floor plan with labeled rooms
    function drawFloorPlan() {
        console.log("🖼️ Redrawing Floor Plan...");
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Set background color for debugging
        ctx.fillStyle = "yellow";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw rooms with borders
        ctx.fillStyle = "lightgray";
        ctx.strokeStyle = "red"; // Red border for debugging
        ctx.lineWidth = 2;

        ctx.fillRect(50, 200, 150, 150);  // Room 1
        ctx.strokeRect(50, 200, 150, 150); // Debug border

        ctx.fillRect(250, 200, 150, 150); // Room 2
        ctx.strokeRect(250, 200, 150, 150);

        ctx.fillRect(50, 50, 150, 150);   // Room 3
        ctx.strokeRect(50, 50, 150, 150);

        ctx.fillRect(250, 50, 150, 150);  // Room 4
        ctx.strokeRect(250, 50, 150, 150);

        // Label rooms
        ctx.fillStyle = "black";
        ctx.font = "16px Arial";
        ctx.fillText("Room 1", 100, 275);
        ctx.fillText("Room 2", 300, 275);
        ctx.fillText("Room 3", 100, 125);
        ctx.fillText("Room 4", 300, 125);
    }

    // Function to update the dot position based on received room data
    function update2DMap(room) {
        drawFloorPlan(); // Redraw floor plan before placing new dot

        if (rooms[room]) {
            ctx.fillStyle = "blue";
            ctx.beginPath();
            ctx.arc(rooms[room].x, rooms[room].y, 10, 0, 2 * Math.PI);
            ctx.fill();
            console.log(`✅ Dot placed in ${room} at (${rooms[room].x}, ${rooms[room].y})`);
        } else {
            console.warn("⚠️ Room not recognized:", room);
        }
    }

    // Initial drawing of the floor plan
    drawFloorPlan();
});
