# coding: UTF-8
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta
import os


host = '192.168.0.8'  # MQTT Broker
port = 1883  # MQTT Port
topic = 'esp32-cam/img'
image_index = 0
client_id = 'python-mqtt'


# MQTT Brokerへの接続する関数
def on_connect(client, userdata, flags, respons_code):
    print('status {0}'.format(respons_code))
    client.subscribe(topic)


# 受信したバイナリデータを output.jpg として保存する関数
def on_message(client, userdata, msg):
    global image_index
    tz_jst = timezone(timedelta(hours=9))  # UTC とは9時間差
    cur_time = datetime.now(tz_jst)
    dirname = './Data/' + cur_time.strftime("%Y%m%d")
    filename = cur_time.strftime("%Y%m%d_%H%M%S") + '.jpg'

    os.makedirs(dirname, exist_ok=True)

    outfile = open(dirname + '/' + filename, 'wb')
    outfile.write(msg.payload)
    outfile.close
    print(filename + " is saved")
    image_index = image_index + 1


if __name__ == '__main__':
    # client = mqtt.Client(protocol=mqtt.MQTTv311)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port=port, keepalive=60)
    client.loop_forever()
