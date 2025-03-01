package com.example.beconlocator

import android.Manifest
import android.annotation.SuppressLint
import android.app.AlertDialog
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var bluetoothAdapter: BluetoothAdapter
    private var bluetoothLeScanner: BluetoothLeScanner? = null
    private lateinit var statusTextView: TextView
    private lateinit var sendDataSwitch: Switch
    private lateinit var userInfoTextView: TextView

    private var isSendingData = false
    private var devicesMap = mutableMapOf<String, BluetoothDevice>()
    private val handler = Handler(Looper.getMainLooper())
    private var userName: String = ""
    private var uniqueID: String = ""

    companion object {
        private const val SERVER_URL ="https://realtimetracking-zcq4.onrender.com/submit-data"
        private const val PERMISSION_REQUEST_CODE = 102
    }

    private val httpClient = OkHttpClient()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize UI elements
        userInfoTextView = findViewById(R.id.userInfoTextView)
        statusTextView = findViewById(R.id.statusTextView)
        sendDataSwitch = findViewById(R.id.sendDataSwitch)

        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter()
        bluetoothLeScanner = bluetoothAdapter.bluetoothLeScanner

        // Get or generate a unique ID
        val sharedPreferences = getSharedPreferences("BeaconLocatorPrefs", Context.MODE_PRIVATE)
        uniqueID = sharedPreferences.getString("uniqueID", UUID.randomUUID().toString()) ?: UUID.randomUUID().toString()
        sharedPreferences.edit().putString("uniqueID", uniqueID).apply()

        requestUserName()
        checkAndRequestPermissions() // Request required permissions

        sendDataSwitch.setOnCheckedChangeListener { _, isChecked ->
            isSendingData = isChecked
            statusTextView.text = if (isChecked) "Status: Available" else "Status: Unavailable"
        }

        // Start scanning automatically if permissions are granted
        if (hasBluetoothPermissions()) {
            startBluetoothScan()
        }
    }

    private fun requestUserName() {
        val sharedPreferences = getSharedPreferences("BeaconLocatorPrefs", Context.MODE_PRIVATE)
        userName = sharedPreferences.getString("userName", "") ?: ""

        if (userName.isEmpty()) {
            val builder = AlertDialog.Builder(this@MainActivity)
            val input = EditText(this@MainActivity)
            input.hint = "Enter your name"
            builder.setTitle("User Name")
                .setView(input)
                .setPositiveButton("OK") { _, _ ->
                    userName = input.text.toString().trim()
                    if (userName.isEmpty()) userName = "Unknown"

                    // Save username so it won't ask again
                    sharedPreferences.edit().putString("userName", userName).apply()

                    userInfoTextView.text = "User: $userName | ID: $uniqueID"
                }
                .setCancelable(false)
                .show()
        } else {
            // If username is already saved, just display it
            userInfoTextView.text = "User: $userName | ID: $uniqueID"
        }
    }


    @SuppressLint("MissingPermission")
    private fun startBluetoothScan() {
        if (!hasBluetoothPermissions()) {
            checkAndRequestPermissions()
            return
        }

        try {
            devicesMap.clear()
            bluetoothLeScanner?.startScan(scanCallback)

            // Restart scan every 10 seconds (to prevent excessive scanning error)
            handler.postDelayed({
                try {
                    bluetoothLeScanner?.stopScan(scanCallback)
                    updateDeviceList()
                    startBluetoothScan()
                } catch (e: SecurityException) {
                    Log.e("MainActivity", "SecurityException while stopping scan: ${e.message}")
                }
            }, 10000)
        } catch (e: SecurityException) {
            Log.e("MainActivity", "SecurityException while starting scan: ${e.message}")
        }
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            if (!hasBluetoothPermissions()) return

            try {
                val device = result.device
                if (!devicesMap.containsKey(device.address) && device.name != null) {
                    devicesMap[device.address] = device
                    Log.d("MainActivity", "Detected: ${device.name} (${device.address})")
                }
            } catch (e: SecurityException) {
                Log.e("MainActivity", "SecurityException in scan callback: ${e.message}")
            }
        }
    }

    private fun updateDeviceList() {
        if (isSendingData) {
            sendDataToServer()
        }
    }

    private fun sendDataToServer() {
        val (room, floor) = determineRoomAndFloor()
        val json = """
            {
                "uniqueID": "$uniqueID",
                "userName": "$userName",
                "room": "$room",
                "floor": $floor,
                "status": "${if (isSendingData) "Available" else "Unavailable"}"
            }
        """.trimIndent()

        CoroutineScope(Dispatchers.IO).launch {
            val requestBody = json.toRequestBody("application/json".toMediaTypeOrNull())
            val request = Request.Builder()
                .url(SERVER_URL)
                .post(requestBody)
                .build()

            try {
                val response = httpClient.newCall(request).execute()
                Log.d("MainActivity", "Response: ${response.body?.string()}")
            } catch (e: Exception) {
                Log.e("MainActivity", "Failed to send data: ${e.message}")
            }
        }
    }

    private fun determineRoomAndFloor(): Pair<String, Int> {
        val mapping = mapOf(
            "Anmol's Phone"  to Pair("Room 1", 1),
            "OnePlus Buds 3" to Pair("Room 2", 1),
            "RoomBeacon3" to Pair("201", 2),
            "RoomBeacon4" to Pair("202", 2),
            "RoomBeacon5" to Pair("301", 3)
        )

        if (!hasBluetoothPermissions()) return Pair("Unknown", -1)

        for (device in devicesMap.values) {
            try {
                if (device.name != null && mapping.containsKey(device.name)) {
                    return mapping[device.name] ?: Pair("Unknown", -1)
                }
            } catch (e: SecurityException) {
                Log.e("MainActivity", "SecurityException in determineRoomAndFloor: ${e.message}")
            }
        }
        return Pair("Unknown", -1)
    }

    private fun hasBluetoothPermissions(): Boolean {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
    }

    private fun checkAndRequestPermissions() {
        val permissions = arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION
        )

        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), PERMISSION_REQUEST_CODE)
        }
    }
}
