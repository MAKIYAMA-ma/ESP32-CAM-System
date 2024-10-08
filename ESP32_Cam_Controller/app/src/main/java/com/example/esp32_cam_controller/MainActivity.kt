package com.example.esp32_cam_controller

import android.app.AlertDialog
import android.content.Context
import android.content.IntentFilter
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import info.mqtt.android.service.MqttAndroidClient
import java.text.SimpleDateFormat
import java.util.Locale
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import org.eclipse.paho.client.mqttv3.*

class MainActivity : AppCompatActivity() {
    private lateinit var mqttClient: MqttAndroidClient
    private var topicEsp32CamControl = "esp32-cam/board/control"
    private var topicEsp32CamSetting = "esp32-cam/board/setting"
    private var topicEsp32SvrControl = "esp32-cam/server/control"
    private var topicEsp32SvrSetting = "esp32-cam/server/setting"
    private var topicEsp32CamImage   = "esp32-cam/img/analyzed"
    private var topicEsp32CurSetting = "esp32-cam/controller/setting"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val cbWarningMainEn = findViewById<CheckBox>(R.id.checkBox_warnMail)
        cbWarningMainEn.isChecked = true

        // val brokerUrl = "tcp://test.mosquitto.org:1883"
        val brokerUrl = "tcp://192.168.0.8:1883"
        val clientId = "ESP32-CAM-Controller"
        mqttClient = MqttAndroidClient(this, brokerUrl, clientId)
        mqttClient.setCallback(object : MqttCallbackExtended {
            override fun connectComplete(reconnect: Boolean, serverURI: String) {
                if (reconnect) {
                    println("Reconnected to: $serverURI")
                    subscribe(topicEsp32CamImage)
                    subscribe(topicEsp32CurSetting)
                } else {
                    println("Connection to: $serverURI")
                }
            }

            override fun connectionLost(cause: Throwable?) {
                println("Connection lost: ${cause?.message}")
            }

            override fun messageArrived(topic: String?, message: MqttMessage?) {
                println("Message arrived: ${message?.toString()}")

                topic?.let {
                    if(topic == topicEsp32CamImage) {
                        message?.payload?.let { payload ->
                            // timestamp:YYYYMMDDHHmmSS
                            val timestampLength = 14
                            if (payload.size >= timestampLength) {
                                val timestampBytes = payload.copyOfRange(0, timestampLength)
                                val timestamp = String(timestampBytes, Charsets.UTF_8)

                                val imageData = payload.copyOfRange(timestampLength, payload.size)

                                println("Timestamp: $timestamp")

                                runOnUiThread {
                                    displayImage(imageData)
                                    displayTimestamp(timestamp)
                                }
                            } else {
                                println("Received payload is too short to contain a timestamp.")
                            }
                        }
                    } else if(topic == topicEsp32CurSetting) {
                        message?.payload?.let { payload ->
                            val jsonElement = Json.parseToJsonElement(String(payload)).jsonObject

                            val hasIntervalShot = "interval_shot" in jsonElement
                            val hasInterval = "interval" in jsonElement
                            val hasWarningMail = "warning_mail" in jsonElement
                            val hasMailAddr = "mail_addr" in jsonElement
                            val hasHumanSensor = "human_sensor" in jsonElement

                            println("interval_shot exists: $hasIntervalShot")
                            println("interval exists: $hasInterval")
                            println("warning_mail exists: $hasWarningMail")
                            println("mail_addr exists: $hasMailAddr")
                            println("human_sensor exists: $hasHumanSensor")

                            try {
                                val setting = Json.decodeFromJsonElement<Setting>(jsonElement)
                                println(setting)

                                if(hasIntervalShot) {
                                    runOnUiThread {
                                        val cbIntervalEn = findViewById<CheckBox>(R.id.checkBox_intervalShot)
                                        cbIntervalEn.isChecked = setting.interval_shot
                                    }
                                    println("interval_shot: " + setting.interval_shot.toString())
                                }
                                if(hasInterval) {
                                    runOnUiThread {
                                        val txtIntervalTime = findViewById<EditText>(R.id.editTextNumber)
                                        txtIntervalTime.setText(setting.interval.toString())
                                    }
                                    println("interval: " + setting.interval.toString())
                                }
                                if(hasWarningMail) {
                                    runOnUiThread {
                                        val cbWarningMainEn = findViewById<CheckBox>(R.id.checkBox_warnMail)
                                        cbWarningMainEn.isChecked = setting.warning_mail
                                    }
                                    println("warning_mail: " + setting.warning_mail.toString())
                                }
                                if(hasMailAddr) {
                                    runOnUiThread {
                                        val txtMailAddr = findViewById<EditText>(R.id.editMailAddr)
                                        txtMailAddr.setText(setting.mail_addr)
                                    }
                                    println("mail_addr: " + setting.mail_addr.toString())
                                }
                                if(hasHumanSensor) {
                                    runOnUiThread {
                                        val cbHumansensorEn = findViewById<CheckBox>(R.id.checkBox_humanSensor)
                                        cbHumansensorEn.isChecked = setting.human_sensor
                                    }
                                    println("human_sensor: " + setting.human_sensor.toString())
                                }
                            } catch (e: SerializationException) {
                                e.printStackTrace()
                            }
                        }
                    } else {
                        // Unknown message
                    }
                }
            }
            override fun deliveryComplete(token: IMqttDeliveryToken?) {
                println("Delivery complete")
            }
        })

        // Connect to MQTT broker
        connect(this)

        // set function of button
        val btShot = findViewById<Button>(R.id.shotButton)
        val btShotListener = ShotButtonListerner()
        btShot.setOnClickListener(btShotListener)

        val btSet = findViewById<Button>(R.id.settingButton)
        val btSetListener = SettingButtonListerner(this)
        btSet.setOnClickListener(btSetListener)
    }

    override fun onDestroy() {
        super.onDestroy()
    }

    companion object {
        const val TAG = "ESP32-CAM-Controller"
    }

    fun connect(context: Context) {
        val options = MqttConnectOptions().apply {
            isAutomaticReconnect = true
            isCleanSession = true
        }
        try {
            mqttClient.connect(options, null, object : IMqttActionListener {
                override fun onSuccess(asyncActionToken: IMqttToken?) {
                    Log.d(TAG, "Connection success")

                    // start subscribe image data
                    subscribe(topicEsp32CamImage)
                    subscribe(topicEsp32CurSetting)
                    reqCurrentSettings()
                }

                override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                    Log.d(TAG, "Connection failure")
                }
            })
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }

    fun subscribe(topic: String, qos: Int = 1) {
        try {
            mqttClient.subscribe(topic, qos, null, object : IMqttActionListener {
                override fun onSuccess(asyncActionToken: IMqttToken?) {
                    Log.d(TAG, "Subscribed to $topic")
                }

                override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                    Log.d(TAG, "Failed to subscribe $topic")
                }
            })
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }

    fun unsubscribe(topic: String) {
        try {
            mqttClient.unsubscribe(topic, null, object : IMqttActionListener {
                override fun onSuccess(asyncActionToken: IMqttToken?) {
                    Log.d(TAG, "Unsubscribed to $topic")
                }

                override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                    Log.d(TAG, "Failed to unsubscribe $topic")
                }
            })
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }

    fun publish(topic: String, msg: String, qos: Int = 1, retained: Boolean = false) {
        try {
            val message = MqttMessage()
            message.payload = msg.toByteArray()
            message.qos = qos
            message.isRetained = retained
            mqttClient.publish(topic, message, null, object : IMqttActionListener {
                override fun onSuccess(asyncActionToken: IMqttToken?) {
                    Log.d(TAG, "$msg published to $topic")
                }

                override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                    Log.d(TAG, "Failed to publish $msg to $topic")
                }
            })
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }

    fun disconnect() {
        try {
            mqttClient.disconnect(null, object : IMqttActionListener {
                override fun onSuccess(asyncActionToken: IMqttToken?) {
                    Log.d(TAG, "Disconnected")
                }

                override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                    Log.d(TAG, "Failed to disconnect")
                }
            })
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }

    private fun displayImage(imageData: ByteArray) {
        val bitmap = BitmapFactory.decodeByteArray(imageData, 0, imageData.size)
        val imageView: ImageView = findViewById(R.id.captureImage)
        imageView.setImageBitmap(bitmap)
    }

    private fun displayTimestamp(timestamp: String) {
        val textView: TextView = findViewById(R.id.textView_timestamp)

        val inputFormat = SimpleDateFormat("yyyyMMddHHmmss", Locale.getDefault())
        val outputFormat = SimpleDateFormat("yyyy/MM/dd HH:mm:ss", Locale.getDefault())

        // タイムスタンプをDate型に変換
        val date = inputFormat.parse(timestamp)

        // Date型を指定のフォーマットの文字列に変換して表示
        textView.text = outputFormat.format(date)
    }

    private fun reqCurrentSettings() {
        publish(topicEsp32CamControl, "{ \"reqset\" : true }")
        publish(topicEsp32SvrControl, "{ \"reqset\" : true }")
    }

    // Listener
    private inner class ShotButtonListerner : View.OnClickListener {
        override fun onClick(view: View) {
            publish(topicEsp32CamControl, "{ \"shot\" : true }")
        }
    }

    private inner class SettingButtonListerner(private val context: Context) : View.OnClickListener {
        override fun onClick(view: View) {
            // publish to server
            val cbWarningMainEn = findViewById<CheckBox>(R.id.checkBox_warnMail)
            val txtMailAddr = findViewById<EditText>(R.id.editMailAddr)

            val enWarningMail = if (cbWarningMainEn.isChecked()) "true" else "false"
            val mailAddr = txtMailAddr.getText().toString()

            val payloadForSvr = "{ \"warning_mail\" : " + enWarningMail + ", \"mail_addr\" : \"" + mailAddr + "\" }";
            publish(topicEsp32SvrSetting, payloadForSvr)

            // publish to board
            val cbIntervalEn = findViewById<CheckBox>(R.id.checkBox_intervalShot)
            val txtIntervalTime = findViewById<EditText>(R.id.editTextNumber)
            val cbHumansensorEn = findViewById<CheckBox>(R.id.checkBox_humanSensor)

            val enIntervalShot = if (cbIntervalEn.isChecked()) "true" else "false"
            val intervalTime = txtIntervalTime.getText().toString()
            val intervalTime_num = intervalTime.toIntOrNull()
            val enHumanSensor = if (cbHumansensorEn.isChecked()) "true" else "false"
            if((intervalTime_num != null) && (intervalTime_num >= 5000)) {
                val payloadForBoard = "{ \"interval_shot\" : " + enIntervalShot +
                                        ", \"interval\" : " + intervalTime +
                                        ", \"human_sensor\" : " + enHumanSensor + "}";
                publish(topicEsp32CamSetting, payloadForBoard)
                AlertDialog.Builder(context)
                    .setTitle("message has been published")
                    .setMessage("interval shot setting message has been published")
                    .setPositiveButton("OK") { dialog, _ ->
                        dialog.dismiss()
                    }
                    .show()
            } else {
                // TODO 警告
                AlertDialog.Builder(context)
                    .setTitle("Error")
                    .setMessage("interval time setting is invalid")
                    .setPositiveButton("OK") { dialog, _ ->
                        dialog.dismiss()
                    }
                    .show()
            }
        }
    }

    @Serializable
    data class Setting(
        val interval_shot: Boolean = false,
        val interval: Int = 10000,
        val warning_mail: Boolean = false,
        val mail_addr: String = "default@example.com",
        val human_sensor: Boolean = false
    )
}
