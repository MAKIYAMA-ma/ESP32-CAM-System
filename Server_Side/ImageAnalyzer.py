# coding: UTF-8
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta
import os
import numpy
import cv2
# import time
from threading import Thread


host = '192.168.0.8'  # MQTT Broker
port = 1883  # MQTT Port
topic = 'esp32-cam/img'
image_index = 0
client_id = 'python-mqtt'

latest_filename = ''
file_changed = False


# MQTT Brokerへの接続する関数
def on_connect(client, userdata, flags, respons_code):
    print('status {0}'.format(respons_code))
    client.subscribe(topic)


# 受信したバイナリデータを output.jpg として保存する関数
def on_message(client, userdata, msg):
    global image_index
    global latest_filename
    global file_changed
    tz_jst = timezone(timedelta(hours=9))  # UTC とは9時間差
    cur_time = datetime.now(tz_jst)
    dirname = './Data/' + cur_time.strftime("%Y%m%d")
    filename = cur_time.strftime("%Y%m%d_%H%M%S") + '.jpg'
    filepath = dirname + '/' + filename

    os.makedirs(dirname, exist_ok=True)

    outfile = open(filepath, 'wb')
    outfile.write(msg.payload)
    outfile.close
    print(filename + " is saved")

    latest_filename = filepath
    file_changed = True

    image_index = image_index + 1


def face_location(input_image_path: str):
    (input_image_basepath, ext) = os.path.splitext(input_image_path)
    output_image_path = input_image_basepath + "_out" + ext

    # 画像を読み込む
    # アルファチャンネル付きに対応するため IMREAD_UNCHANGED を使う
    # cv2.IMREAD_COLOR	画像をカラー(RGB)で読込む。 引数のデフォルト値。
    # cv2.IMREAD_GRAYSCALE	画像をグレースケールで読込む。
    # cv2.IMREAD_UNCHANGED	画像を RGB に透過度を加えた RGBA で読込む。
    print("[DEBUG] input_image_path:" + input_image_path)
    print("[DEBUG] input_image:")
    print(os.path.isfile(input_image_path))
    input_image = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)

    # Haar 特徴ベースのカスケード分類器による物体検出の準備
    # 顔検出用のカスケード分類器を使用
    # 以下の識別器がある
    # haarcascade_eye.xml	目
    # haarcascade_eye_tree_eyeglasses.xml	メガネ
    # haarcascade_frontalcatface.xml	猫の顔（正面）
    # haarcascade_frontalcatface_extended.xml	猫の顔（正面）
    # haarcascade_frontalface_alt.xml	顔（正面）
    # haarcascade_frontalface_alt2.xml	顔（正面）
    # haarcascade_frontalface_alt_tree.xml	顔（正面）
    # haarcascade_frontalface_default.xml	顔（正面）
    # haarcascade_fullbody.xml	全身
    # haarcascade_lefteye_2spits.xml	左目
    # haarcascade_licence_plate_rus_16stages.xml	ロシアのナンバープレート（全体）
    # haarcascade_lowerbody.xml	下半身
    # haarcascade_profileface.xml	顔（証明写真）
    # haarcascade_righteye_2splits.xml	右目
    # haarcascade_russian_plate_number.xml	笑顔
    # haarcascade_upperbody.xml	上半身
    face_cascade_name = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    # face_cascade_name = cv2.data.haarcascades + "haarcascade_frontalcatface_extended.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_name)

    # 顔を検出
    faces = face_cascade.detectMultiScale(input_image)

    # 出力画像データを入れるオブジェクト
    # 入力画像データを出力画像データにコピー
    output_image = numpy.copy(input_image)
    print("[DEBUG] inputimage:")
    print(input_image)
    print("[DEBUG] outputimage:")
    print(output_image)

    for (x, y, w, h) in faces:
        # 検出した顔の座標を出力
        print("Face: [{} x {} from ({}, {})]".format(w, h, x, y))

        # 顔の位置に楕円を描画
        # //は切り捨て除算
        center = (x + w // 2, y + h // 2)
        size = (w // 2, h // 2)
        angle = 0
        startAngle = 0
        endAngle = 360
        color = (127, 0, 255, 255)  # Blue, Green, Red, Alpha
        thickness = 4
        cv2.ellipse(output_image, center, size, angle, startAngle, endAngle, color, thickness)

    # 画像を出力
    print(input_image_path)
    print(output_image_path)
    cv2.imwrite(output_image_path, output_image)


def mqtt_sub_task():
    # client = mqtt.Client(protocol=mqtt.MQTTv311)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port=port, keepalive=60)
    client.loop_forever()


def image_analyze_task():
    global file_changed
    global latest_filename

    while True:
        if file_changed:
            face_location(latest_filename)
            file_changed = False


if __name__ == '__main__':
    mqtt_thread = Thread(target=mqtt_sub_task)
    mqtt_thread.start()

    face_analyze_thread = Thread(target=image_analyze_task)
    face_analyze_thread.start()
