package com.example.esp32_cam_controller

import android.os.Bundle
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import org.eclipse.paho.android.service.MqttAndroidClient
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
    private lateinit var receiver: MyReceiver

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
        val clientId = "KotlinAndroidClient"
        mqttClient = MqttAndroidClient(this, brokerUrl, clientId)

        val existingCallback = object : MqttCallback {
            override fun connectionLost(cause: Throwable?) {
                println("Connection lost: ${cause?.message}")
            }

            override fun messageArrived(topic: String?, message: MqttMessage?) {
                println("Message arrived: ${message?.toString()}")
            }

            override fun deliveryComplete(token: IMqttDeliveryToken?) {
                println("Delivery complete")
            }
        }

        val customCallback = CustomMqttCallback(this, existingCallback)
        mqttClient.setCallback(customCallback)

        receiver = MyReceiver()
        val filter = IntentFilter("android.net.conn.CONNECTIVITY_CHANGE")
        registerReceiver(receiver, filter)

        connectAndPublish()
    }

    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(receiver)
    }

    private fun connectAndPublish() {
        println("connectAndPublish");

        try {
            val options = MqttConnectOptions().apply {
                isAutomaticReconnect = true
                isCleanSession = true
            }

            mqttClient.connect(options, null, object : IMqttActionListener {
                override fun onSuccess(asyncActionToken: IMqttToken?) {
                    println("Connected to broker")

                    val topic = "test/topic"
                    val message = MqttMessage("Hello from Android Kotlin".toByteArray())
                    message.qos = 2

                    mqttClient.publish(topic, message, null, object : IMqttActionListener {
                        override fun onSuccess(asyncActionToken: IMqttToken?) {
                            println("Message published")
                        }

                        override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                            println("Failed to publish message: ${exception?.message}")
                        }
                    })
                }

                override fun onFailure(asyncActionToken: IMqttToken?, exception: Throwable?) {
                    println("Failed to connect to broker: ${exception?.message}")
                }
            })
        } catch (e: MqttException) {
            e.printStackTrace()
        }
    }
}
