package com.example.bluetoothbecon1

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.*
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var bluetoothAdapter: BluetoothAdapter
    private var bluetoothLeAdvertiser: BluetoothLeAdvertiser? = null

    private val advertiseCallback = object : AdvertiseCallback() {
        override fun onStartSuccess(settingsInEffect: AdvertiseSettings) {
            super.onStartSuccess(settingsInEffect)
            Toast.makeText(this@MainActivity, "BLE Advertising Started", Toast.LENGTH_SHORT).show()
            Log.d("BLE", "Advertising started successfully")
        }

        override fun onStartFailure(errorCode: Int) {
            super.onStartFailure(errorCode)
            val errorMessage = when (errorCode) {
                ADVERTISE_FAILED_ALREADY_STARTED -> "Advertising already started"
                ADVERTISE_FAILED_DATA_TOO_LARGE -> "Advertising data too large"
                ADVERTISE_FAILED_TOO_MANY_ADVERTISERS -> "Too many advertisers"
                ADVERTISE_FAILED_INTERNAL_ERROR -> "Internal error"
                ADVERTISE_FAILED_FEATURE_UNSUPPORTED -> "Feature unsupported"
                else -> "Unknown error"
            }
            Toast.makeText(this@MainActivity, "Advertising Failed: $errorMessage", Toast.LENGTH_SHORT).show()
            Log.e("BLE", "Advertising failed: $errorMessage")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        checkPermissions() // Request necessary permissions

        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter

        if (bluetoothAdapter.isMultipleAdvertisementSupported) {
            startAdvertising()
        } else {
            Toast.makeText(this, "BLE advertising not supported on this device", Toast.LENGTH_SHORT).show()
        }
    }

    private fun checkPermissions() {
        val permissions = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) { // Android 12+
            permissions.add(Manifest.permission.BLUETOOTH_ADVERTISE)
            permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            permissions.add(Manifest.permission.BLUETOOTH)
            permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
        }

        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), 1)
        }
    }

    private fun startAdvertising() {
        bluetoothLeAdvertiser = bluetoothAdapter.bluetoothLeAdvertiser
        if (bluetoothLeAdvertiser == null) {
            Toast.makeText(this, "Failed to get BLE Advertiser", Toast.LENGTH_SHORT).show()
            return
        }

        // **Optimized Settings for Maximum Detection Range**
        val advertisingSettings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY) // Best for detection
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH) // Maximum TX power
            .setConnectable(false)
            .setTimeout(0) // No timeout
            .build()

        val manufacturerId = 0xFFFF  // Custom manufacturer ID
        val manufacturerData = byteArrayOf(0x01, 0x02, 0x03, 0x04) // Some random bytes

        val advertisingData = AdvertiseData.Builder()
            .setIncludeDeviceName(true) // Include name for easy scanning
            .addManufacturerData(manufacturerId, manufacturerData) // Add manufacturer data
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED
        ) {
            Toast.makeText(this, "Bluetooth advertising permission not granted", Toast.LENGTH_SHORT).show()
            return
        }

        bluetoothLeAdvertiser?.startAdvertising(advertisingSettings, advertisingData, advertiseCallback)
    }

    override fun onDestroy() {
        super.onDestroy()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED
        ) {
            return
        }
        bluetoothLeAdvertiser?.stopAdvertising(advertiseCallback)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                startAdvertising() // Start advertising after permissions are granted
            } else {
                Toast.makeText(this, "Permissions denied. Advertising will not work.", Toast.LENGTH_SHORT).show()
            }
        }
    }
}
