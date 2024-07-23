package com.example.esp32_cam_controller

import android.os.Bundle
import android.content.Context
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.CheckBox
import android.widget.ImageView
import android.widget.RadioGroup
import android.widget.RadioButton
import android.graphics.BitmapFactory
import android.app.AlertDialog
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import info.mqtt.android.service.MqttAndroidClient
import org.eclipse.paho.client.mqttv3.*
import android.content.IntentFilter

class MainActivity : AppCompatActivity() {
    private lateinit var mqttClient: MqttAndroidClient
    private var topicEsp32CamControl = "esp32-cam/board/control"
    private var topicEsp32CamSetting = "esp32-cam/board/setting"
    private var topicEsp32SvrSetting = "esp32-cam/server/setting"
    private var topicEsp32CamImage = "esp32-cam/img/#"
    private var topicEsp32CamRawImage = "esp32-cam/img/raw"
    private var topicEsp32CamProcessedImage = "esp32-cam/img/processed"

    private var showProcessedImage = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val imageTypeRadioGroup = findViewById<RadioGroup>(R.id.imageType_radioGroup)
        val radioButtonProcessedImage = findViewById<RadioButton>(R.id.radioButton_processedImage)
        val radioButtonRawImage = findViewById<RadioButton>(R.id.radioButton_rawImage)
        val sendPathRadioGroup = findViewById<RadioGroup>(R.id.sendPath_radioGroup)
        val radioButtonSendMqtt = findViewById<RadioButton>(R.id.radioButton_sendMqtt)

        // ラジオボタンの連動設定
        imageTypeRadioGroup.setOnCheckedChangeListener { _, checkedId ->
            when (checkedId) {
                R.id.radioButton_processedImage -> {
                    // processedImage が選択された場合,MQTT固定
                    radioButtonSendMqtt.isChecked = true
                    setRadioGroupEnabled(sendPathRadioGroup, false)
                }
                R.id.radioButton_rawImage -> {
                    // rawImage が選択された場合
                    setRadioGroupEnabled(sendPathRadioGroup, true)
                }
            }
        }
        imageTypeRadioGroup.check(R.id.radioButton_rawImage)
        sendPathRadioGroup.check(R.id.radioButton_sendMqtt)

        val brokerUrl = "tcp://192.168.0.8:1883"
        val clientId = "ESP32-CAM-Controller"
        mqttClient = MqttAndroidClient(this, brokerUrl, clientId)
        mqttClient.setCallback(object : MqttCallbackExtended {
            override fun connectComplete(reconnect: Boolean, serverURI: String) {
                if (reconnect) {
                    println("Reconnected to: $serverURI")
                    subscribe(topicEsp32CamImage)   // TODO 利用するのは常にどちらか一方。必要な方のみsubscribeするほうが良い。
                } else {
                    println("Connection to: $serverURI")
                }
            }

            override fun connectionLost(cause: Throwable?) {
                println("Connection lost: ${cause?.message}")
            }

            override fun messageArrived(topic: String?, message: MqttMessage?) {
                println("Message arrived: ${message?.toString()}")
                if ((showProcessedImage && (topic == topicEsp32CamProcessedImage)) ||
                    (!showProcessedImage && (topic == topicEsp32CamRawImage))) {
                    // image data is received
                    message?.payload?.let {
                        runOnUiThread {
                            displayImage(it)
                        }
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

    private fun setRadioGroupEnabled(radioGroup: RadioGroup, enabled: Boolean) {
        for (i in 0 until radioGroup.childCount) {
            val child = radioGroup.getChildAt(i)
            child.isEnabled = enabled
        }
    }

    // Listener
    private inner class ShotButtonListerner : View.OnClickListener {
        override fun onClick(view: View) {
            publish(topicEsp32CamControl, "{ \"shot\" : true }")
        }
    }

    private inner class SettingButtonListerner(private val context: Context) : View.OnClickListener {
        override fun onClick(view: View) {
            val cbIntervalEn = findViewById<CheckBox>(R.id.checkBox_intervalShot)
            val txtIntervalTime = findViewById<EditText>(R.id.editTextNumber)
            val imageTypeRadioGroup = findViewById<RadioGroup>(R.id.imageType_radioGroup)
            val imageTypeId = imageTypeRadioGroup.checkedRadioButtonId
            val sendPathRadioGroup = findViewById<RadioGroup>(R.id.sendPath_radioGroup)
            val sendPathId = sendPathRadioGroup.checkedRadioButtonId

            val enIntervalShot = if (cbIntervalEn.isChecked()) "true" else "false"
            val intervalTime = txtIntervalTime.getText().toString()
            val intervalTime_num = intervalTime.toIntOrNull()

            // publish to server
            var sendImagePath = "mqtt"
            when(sendPathId) {
                R.id.radioButton_noSend -> { sendImagePath = "none" }
                R.id.radioButton_sendMail -> { sendImagePath = "mail" }
                R.id.radioButton_sendMqtt -> { sendImagePath = "mqtt" }
            }
            showProcessedImage = (imageTypeId == R.id.radioButton_processedImage)
            val sendProcessedImage = if (showProcessedImage) "processed" else "raw"
            val payloadForSvr = "{ \"send_image\" : \"" + sendImagePath + "\", \"image_type\" : \"" + sendProcessedImage + "\" }";
            publish(topicEsp32SvrSetting, payloadForSvr)

            // TODO set send type
            // If "show processed image" mode, MQTT must be selected

            // publish to board
            if((intervalTime_num != null) && (intervalTime_num >= 5000)) {
                val payload = "{ \"interval_shot\" : " + enIntervalShot + ", \"interval\" : " + intervalTime + "}";
                publish(topicEsp32CamSetting, payload)
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
}
