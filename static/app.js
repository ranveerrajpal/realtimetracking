document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("floorCanvas");
    const ctx = canvas.getContext("2d");

    if (!canvas || !ctx) {
        console.error("❌ Canvas element not found!");
        return;
    }

    console.log("🚀 Initializing 2D Map...");

    // Define room positions on the canvas
    const rooms = {
        "Room 1": { x: 125, y: 275 },
        "Room 2": { x: 325, y: 275 },
        "Room 3": { x: 125, y: 125 },
        "Room 4": { x: 325, y: 125 }
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

    function drawFloorPlan() {
        console.log("🖼️ Redrawing Floor Plan...");
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

    function update2DMap(room) {
        drawFloorPlan();

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

    drawFloorPlan();
});
