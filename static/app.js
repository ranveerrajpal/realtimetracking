document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("floorCanvas");
    const ctx = canvas.getContext("2d");

    // Define room positions (adjust X, Y based on actual map layout)
    const rooms = {
        "Room 1": { x: 100, y: 250 },
        "Room 2": { x: 300, y: 250 },
        "Room 3": { x: 100, y: 100 },
        "Room 4": { x: 300, y: 100 }
    };

    // WebSocket Connection
    const socket = new WebSocket("wss://realtimetracking-zcq4.onrender.com/ws");

    socket.onopen = () => {
        console.log("✅ WebSocket connection established.");
    };

    socket.onmessage = (event) => {
        console.log("📩 Received Data:", event.data);
        try {
            const data = JSON.parse(event.data);
            if (data.room && rooms[data.room]) {
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
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw rooms
        ctx.fillStyle = "lightgray";
        ctx.fillRect(50, 200, 150, 150);  // Room 1
        ctx.fillRect(250, 200, 150, 150); // Room 2
        ctx.fillRect(50, 50, 150, 150);   // Room 3
        ctx.fillRect(250, 50, 150, 150);  // Room 4

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
        drawFloorPlan(); // Redraw the floor plan to clear previous dots

        if (rooms[room]) {
            ctx.fillStyle = "blue";
            ctx.beginPath();
            ctx.arc(rooms[room].x, rooms[room].y, 10, 0, 2 * Math.PI);
            ctx.fill();
            console.log(`✅ Dot updated in ${room} at (${rooms[room].x}, ${rooms[room].y})`);
        } else {
            console.warn("⚠️ Room not recognized:", room);
        }
    }

    // Initial drawing of the floor plan
    drawFloorPlan();
});
