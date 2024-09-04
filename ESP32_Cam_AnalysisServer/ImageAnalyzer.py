# coding: UTF-8
# import compare_face
# import time
# import util
from PIL import Image
from compare_face import Comparator
from datetime import datetime, timezone, timedelta
from notification import Mailer
from threading import Thread
import cv2
import io
import json
import numpy
import os
import paho.mqtt.client as mqtt
import queue


class mode_singleton:
    _instance = None
    en_warning_mail = True
    mailer = Mailer()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(mode_singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def set_waining_mail(self, value):
        mode_singleton.en_warning_mail = value

    def get_waining_mail(self):
        return mode_singleton.en_warning_mail

    def get_mailer(self):
        return mode_singleton.mailer

    def set_mailer_to(self, addr: str):
        self.mailer.set_to(addr)

    def get_mailer_to(self):
        return self.mailer.get_to()


class mqtt_task:
    client = None
    queue = None

    # MQTT parameters
    # host = 'test.mosquitto.org'  # MQTT Broker
    host = '192.168.0.8'  # MQTT Broker
    port = 1883  # MQTT Port
    topic_img = 'esp32-cam/img/raw'
    topic_sub = 'esp32-cam/server/#'
    topic_control = 'esp32-cam/server/control'
    topic_setting = 'esp32-cam/server/setting'
    topic_pub_img = 'esp32-cam/img/analyzed'
    topic_pub_img_scale = 'esp32-cam/img/analyzed_scale'
    topic_pub_setting = 'esp32-cam/controller/setting'
    topic_pub_control = 'esp32-cam/board/control'
    client_id = 'python-mqtt'

    def __init__(self, queue):
        self.queue = queue
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, respons_code):
        print('status {0}'.format(respons_code))
        client.subscribe(self.topic_sub)
        client.subscribe(self.topic_img)
        self.publish_setting()

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
        elif msg.topic == self.topic_control:
            received_data = json.loads(msg.payload)
            if received_data.get("reqset", False):
                self.publish_setting()
        elif msg.topic == self.topic_setting:
            mode = mode_singleton()
            received_data = json.loads(msg.payload)
            mode.set_waining_mail(received_data.get("warning_mail", True))
            mode.set_mailer_to(received_data.get("mail_addr"))

    def publish_image(self, payload):
        self.client.publish(self.topic_pub_img, payload=payload, qos=1, retain=False)

    def publish_image_scale(self, payload):
        self.client.publish(self.topic_pub_img_scale, payload=payload, qos=1, retain=False)

    def publish_setting(self):
        mode = mode_singleton()
        payload = "{"
        payload += "\"warning_mail\": " + ("true" if mode.get_waining_mail() else "false")
        payload += ", \"mail_addr\" :\"" + mode.get_mailer_to() + "\" }"
        self.client.publish(self.topic_pub_setting, payload=payload, qos=1, retain=False)

    def publish_text(self, text: str):
        payload = "{ \"text\" :\"" + text + "\" }"
        self.client.publish(self.topic_pub_control, payload=payload, qos=1, retain=False)

    def run(self):
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

    def change_bmp_img(self, jpg_image):
        # バイナリデータをBytesIOに変換
        image_stream = io.BytesIO(jpg_image)

        # JPEGイメージを開く
        image = Image.open(image_stream)

        # 16ビットカラーに変換
        # 16ビットカラー (RGB565) の代わりに、Pillowは 8 ビットチャンネルごとの RGB に変換しますが、
        # これを疑似的に 16 ビットカラー相当として扱います。
        image = image.convert("RGB")

        bmp_data = io.BytesIO()
        image.save(bmp_data, format="BMP")
        bmp_data = bmp_data.getvalue()

        return bmp_data

    def resize_image(self, image_data, scale=0.5):
        image = Image.open(io.BytesIO(image_data))

        new_size = (int(image.width * scale), int(image.height * scale))

        resized_image = image.resize(new_size, Image.LANCZOS)

        img_byte_arr = io.BytesIO()
        resized_image.save(img_byte_arr, format=image.format)
        img_byte_arr = img_byte_arr.getvalue()

        return img_byte_arr

    def make_color_bar(self, width=160, height=120):
        image = Image.new("RGB", (width, height))
        pixels = image.load()

        for y in range(height):
            if (y // 10) % 5 == 0:
                color = (255, 0,   0)    # Red
            elif (y // 10) % 5 == 1:
                color = (0,   255, 0)    # Green
            elif (y // 10) % 5 == 2:
                color = (0,   0,   255)  # Blue
            elif (y // 10) % 5 == 3:
                color = (0,   0,   0)    # Black
            else:
                color = (255, 255, 255)  # White

            for x in range(width):
                pixels[x, y] = color

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        image.save("./re1.jpg", format='JPEG')
        image = image.convert("RGB")
        image.save("./re2.jpg", format='JPEG')
        image = image.convert("YCbCr")
        image.save("./re3.jpg", format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        return img_byte_arr

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

                # ファイル名部分が日時
                # 本当はBoard側で撮影の瞬間のタイムスタンプをつけたいが
                # RTCとかないので。。。
                timestamp = os.path.splitext(os.path.basename(latest_filename))[0]

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
                        self.taskm.publish_text("[" + timestamp + "] Registerd person detected")
                    else:
                        msg = "NOT registerd person detected[" + str(sims) + "]\n"
                        msg = msg + "time:" + timestamp
                        print(msg)
                        self.taskm.publish_text("[" + timestamp + "] NOT registerd person detected")
                        if mode.get_waining_mail():
                            mode.get_mailer().main("UNKNWON person was detected!!", msg, file_to_send)
                else:
                    self.taskm.publish_text("[" + timestamp + "] No person detected")
                    print("No person detected")

                # send via MQTT
                image_data = None
                with open(file_to_send, "rb") as image_file:
                    if True:
                        # send as jpeg
                        image_data = image_file.read()
                    else:
                        # send as bmp
                        image_data = self.change_bmp_img(image_file.read())

                if image_data is not None:
                    # resize_image_data = self.resize_image(image_data, scale=0.5)
                    resize_image_data = self.make_color_bar()
                    timestamp_bytedata = timestamp.replace('_', '').encode('utf-8')
                    self.taskm.publish_image(timestamp_bytedata + image_data)
                    self.taskm.publish_image_scale(resize_image_data)
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
