package com.example.esp32_cam_controller

import android.content.Context
import org.eclipse.paho.client.mqttv3.*
import org.eclipse.paho.client.mqttv3.internal.ClientComms

class CustomMqttCallback(
    private val context: Context,
    private val delegate: MqttCallback
) : MqttCallback, MqttPingSender {

    private lateinit var customPingSender: CustomPingSender
    private lateinit var comms: ClientComms

    init {
        customPingSender = CustomPingSender(context)
    }

    override fun connectionLost(cause: Throwable?) {
        delegate.connectionLost(cause)
    }

    override fun messageArrived(topic: String?, message: MqttMessage?) {
        delegate.messageArrived(topic, message)
    }

    override fun deliveryComplete(token: IMqttDeliveryToken?) {
        delegate.deliveryComplete(token)
    }

    override fun init(comms: ClientComms) {
        this.comms = comms
        customPingSender.init(comms)
    }

    override fun start() {
        customPingSender.start()
    }

    override fun stop() {
        customPingSender.stop()
    }

    override fun schedule(delayInMilliseconds: Long) {
        customPingSender.schedule(delayInMilliseconds)
    }
}
