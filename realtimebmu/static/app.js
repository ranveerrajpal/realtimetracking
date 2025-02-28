document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("floorCanvas");
    const ctx = canvas.getContext("2d");

    let users = {}; // Store user locations

    // WebSocket Setup
    const ws = new WebSocket("wss://your-app-name.onrender.com/ws");

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        users[data.unique_id] = { room_no: data.room_no };
        drawFloorPlan();

        // Update 3D Position
        const userDot = document.getElementById("userDot");
        if (data.room_no === 101) {
            userDot.setAttribute("position", "-1 0.2 -1");
        } else if (data.room_no === 102) {
            userDot.setAttribute("position", "1 0.2 -1");
        }
    };

    function drawFloorPlan() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Corridor
        ctx.fillStyle = "gray";
        ctx.fillRect(200, 150, 100, 200);

        // Room 101 (Left)
        ctx.fillStyle = "lightblue";
        ctx.fillRect(50, 150, 150, 200);
        ctx.fillStyle = "black";
        ctx.fillText("Room 101", 90, 180);

        // Room 102 (Top Right at 90 degrees)
        ctx.fillStyle = "lightgreen";
        ctx.fillRect(200, 50, 200, 100);
        ctx.fillStyle = "black";
        ctx.fillText("Room 102", 260, 80);

        // Draw Blue Dots
        for (let userId in users) {
            let user = users[userId];
            let x, y;

            if (user.room_no === 101) {
                x = 100;
                y = 250;
            } else if (user.room_no === 102) {
                x = 250;
                y = 75;
            }

            ctx.fillStyle = "blue";
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    drawFloorPlan();
});
