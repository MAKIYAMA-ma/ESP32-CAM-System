package com.example.esp32_cam_controller

import android.os.Bundle
import android.content.Context
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.CheckBox
import android.widget.ImageView
import android.graphics.BitmapFactory
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import info.mqtt.android.service.MqttAndroidClient
import org.eclipse.paho.client.mqttv3.IMqttActionListener
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken
import org.eclipse.paho.client.mqttv3.IMqttToken
import org.eclipse.paho.client.mqttv3.MqttCallback
import org.eclipse.paho.client.mqttv3.MqttMessage
import org.eclipse.paho.client.mqttv3.MqttConnectOptions
import org.eclipse.paho.client.mqttv3.MqttException
import org.eclipse.paho.client.mqttv3.MqttClient
import android.content.IntentFilter

class MainActivity : AppCompatActivity() {
    private lateinit var mqttClient: MqttAndroidClient
    private var topicEsp32CamControl = "esp32-cam/control"
    private var topicEsp32CamImage = "esp32-cam/img"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val brokerUrl = "tcp://192.168.0.8:1883"
        val clientId = "ESP32-CAM-Controller"
        mqttClient = MqttAndroidClient(this, brokerUrl, clientId)
        mqttClient.setCallback(object : MqttCallback {
            override fun connectionLost(cause: Throwable?) {
                println("Connection lost: ${cause?.message}")
            }

            override fun messageArrived(topic: String?, message: MqttMessage?) {
                println("Message arrived: ${message?.toString()}")
                if (topic == topicEsp32CamImage) {
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
        val btSetListener = SettingButtonListerner()
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

    // Listener
    private inner class ShotButtonListerner : View.OnClickListener {
        override fun onClick(view: View) {
            publish(topicEsp32CamControl, "{ \"shot\" : true }")
        }
    }

    private inner class SettingButtonListerner : View.OnClickListener {
        override fun onClick(view: View) {
            val cbIntervalEn = findViewById<CheckBox>(R.id.checkBox_intervalShot)
            val txtIntervalTime = findViewById<EditText>(R.id.editTextNumber)

            val enIntervalShot = if (cbIntervalEn.isChecked()) "true" else "false"
            val intervalTime = txtIntervalTime.getText().toString()
            val intervalTime_num = intervalTime.toIntOrNull()

            if((intervalTime_num != null) && (intervalTime_num >= 5000)) {
                val payload = "{ \"interval_shot\" : " + enIntervalShot + ", \"interval\" : " + intervalTime + "}";
                publish(topicEsp32CamControl, payload)
            } else {
                // TODO 警告
            }
        }
    }
}
