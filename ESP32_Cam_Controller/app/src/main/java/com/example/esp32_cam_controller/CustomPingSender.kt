package com.example.esp32_cam_controller

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.SystemClock
import org.eclipse.paho.client.mqttv3.internal.ClientComms
import org.eclipse.paho.client.mqttv3.internal.wire.MqttPingReq
import org.eclipse.paho.client.mqttv3.logging.JSR47Logger
import org.eclipse.paho.client.mqttv3.MqttPingSender

class CustomPingSender(private val context: Context) : BroadcastReceiver(), MqttPingSender {
    private lateinit var comms: ClientComms
    private val alarmMgr: AlarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
    private lateinit var pendingIntent: PendingIntent

    override fun init(comms: ClientComms) {
        this.comms = comms
        val filter = IntentFilter("com.example.esp32_cam_controller.PING")
        context.registerReceiver(this, filter)
        pendingIntent = PendingIntent.getBroadcast(context, 0, Intent("com.example.esp32_cam_controller.PING"), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }

    override fun start() {
        schedule(comms.keepAlive)
    }

    override fun stop() {
        alarmMgr.cancel(pendingIntent)
        context.unregisterReceiver(this)
    }

    override fun schedule(delayInMilliseconds: Long) {
        val triggerAt = SystemClock.elapsedRealtime() + delayInMilliseconds
        alarmMgr.setExactAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, triggerAt, pendingIntent)
    }

    override fun onReceive(context: Context?, intent: Intent?) {
        if (comms.isConnected) {
            try {
                val pingReq = MqttPingReq()
                comms.sendNoWait(pingReq, null)
                schedule(comms.keepAlive)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    companion object {
        private val log = JSR47Logger::class.java.name
    }
}
