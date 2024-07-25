# coding: UTF-8
import paho.mqtt.client as mqtt
from datetime import datetime, timezone, timedelta
import os
import numpy
import cv2
# import time
from threading import Thread
import queue
# import compare_face
from compare_face import Comparator
# import util
import notification
import json


class mode_singleton:
    _instance = None
    en_warning_mail = True

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(mode_singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def set_waining_mail(self, value):
        mode_singleton.en_warning_mail = value

    def get_waining_mail(self):
        return mode_singleton.en_warning_mail


class mqtt_task:
    host = '192.168.0.8'  # MQTT Broker
    port = 1883  # MQTT Port
    topic_img = 'esp32-cam/img/raw'
    # topic_sub = 'esp32-cam/#'
    topic_sub = 'esp32-cam/server/#'
    topic_control = 'esp32-cam/server/control'
    topic_setting = 'esp32-cam/server/setting'
    topic_pub = 'esp32-cam/img/analyzed'
    image_index = 0
    client_id = 'python-mqtt'
    client = None

    queue = None

    def __init__(self, queue):
        self.queue = queue

    def on_connect(self, client, userdata, flags, respons_code):
        print('status {0}'.format(respons_code))
        client.subscribe(self.topic_sub)
        client.subscribe(self.topic_img)

    # 受信したバイナリデータを output.jpg として保存する関数
    def on_message(self, client, userdata, msg):
        if msg.topic == self.topic_img:
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

            self.queue.put(filepath, timeout=1)
            self.image_index = self.image_index + 1
        elif msg.topic == self.topic_control:
            # NOP
            pass
        elif msg.topic == self.topic_setting:
            # TODO
            mode = mode_singleton()
            received_data = json.loads(msg.payload)
            warning_mail_value = received_data.get("warning_mail", True)
            mail_addr_value = received_data.get("mail_addr")

            mode.set_waining_mail(warning_mail_value)

            # TODO handling of mail_addr_value

    def publish(self, payload):
        self.client.publish(self.topic_pub, payload=payload, qos=1, retain=False)

    def run(self):
        # client = mqtt.Client(protocol=mqtt.MQTTv311)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.host, port=self.port, keepalive=60)
        self.client.loop_forever()


class face_analyze_task:
    queue = None
    taskm = None

    def __init__(self, queue, taskm):
        self.queue = queue
        self.taskm = taskm

    def face_location(self, input_image_path: str):
        (input_image_basepath, ext) = os.path.splitext(input_image_path)
        output_image_path = input_image_basepath + "_out" + ext

        # 画像を読み込む
        # アルファチャンネル付きに対応するため IMREAD_UNCHANGED を使う
        # cv2.IMREAD_COLOR	画像をカラー(RGB)で読込む。 引数のデフォルト値。
        # cv2.IMREAD_GRAYSCALE	画像をグレースケールで読込む。
        # cv2.IMREAD_UNCHANGED	画像を RGB に透過度を加えた RGBA で読込む。
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

        if len(faces) != 0:
            print(input_image_path + ":Human!")
            for (x, y, w, h) in faces:
                # 検出した顔の座標を出力
                # print("Face: [{} x {} from ({}, {})]".format(w, h, x, y))

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
            cv2.imwrite(output_image_path, output_image)
            return (True, output_image_path)
        else:
            print(input_image_path + ":NOT Human!")
            return (False, "")

    def face_exist(self, input_image_path: str):
        (input_image_basepath, ext) = os.path.splitext(input_image_path)

        input_image = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
        face_cascade_name = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(face_cascade_name)

        # 顔を検出
        faces = face_cascade.detectMultiScale(input_image)

        return (len(faces) != 0)

    def run(self):
        try:
            comparotor = Comparator()
            comparotor.save_regfaces()
            mode = mode_singleton()

            while True:
                latest_filename = self.queue.get()

                (face_exist, processed_filename) = self.face_location(latest_filename)
                if processed_filename != "":
                    file_to_send = processed_filename
                else:
                    file_to_send = latest_filename

                if face_exist:
                    sims = comparotor.get_reg_sim(latest_filename)
                    sims_list = [item for sublist in sims for item in sublist]
                    if len(sims_list) > 0:
                        max_sim = max(sims_list)
                    else:
                        max_sim = 0
                    # 登録されている人が混じっているならOKとする
                    if max_sim > 0.35:
                        print("Registerd person detected[" + str(sims) + "]")
                    else:
                        msg = "NOT registerd person detected[" + str(sims) + "]"
                        print(msg)
                        if mode.get_waining_mail():
                            notification.main("UNKNWON person was detected!!", msg, file_to_send)
                else:
                    print("No person detected")

                # send via MQTT
                image_data = None
                with open(file_to_send, "rb") as image_file:
                    image_data = image_file.read()

                if image_data is not None:
                    self.taskm.publish(image_data)
        except KeyboardInterrupt:
            pass


def main():
    image_queue = queue.Queue()
    taskm = mqtt_task(image_queue)
    taskf = face_analyze_task(image_queue, taskm)

    mqtt_thread = Thread(target=taskm.run)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    face_analyze_thread = Thread(target=taskf.run)
    face_analyze_thread.daemon = True
    face_analyze_thread.start()

    while True:
        pass


if __name__ == '__main__':
    main()
