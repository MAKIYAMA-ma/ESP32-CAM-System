# coding: UTF-8
import os
import sys
import cv2
import numpy


def face_location(dirpath: str, filename: str):
    (filename_tag, ext) = os.path.splitext(filename)

    # 画像を読み込む
    # アルファチャンネル付きに対応するため IMREAD_UNCHANGED を使う
    # cv2.IMREAD_COLOR	画像をカラー(RGB)で読込む。 引数のデフォルト値。
    # cv2.IMREAD_GRAYSCALE	画像をグレースケールで読込む。
    # cv2.IMREAD_UNCHANGED	画像を RGB に透過度を加えた RGBA で読込む。
    # input_image = cv2.imread(os.path.join(dirpath, filename), cv2.IMREAD_UNCHANGED)
    input_image = imread(os.path.join(dirpath, filename), flags=cv2.IMREAD_UNCHANGED)

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

    if len(faces) != 0:
        face_cnt = 0
        output_dir = os.path.join(dirpath, 'face')
        os.makedirs(output_dir, exist_ok=True)
        for (x, y, w, h) in faces:
            output_file_name = filename_tag + '_face' + str(face_cnt) + ext
            output_image_path = os.path.join(output_dir, output_file_name)
            face_cnt = face_cnt + 1
            output_image = input_image[y:y+h, x:x+w]
            print(output_image_path)
            imwrite(output_image_path, output_image)
            # cv2.imwrite(output_image_path, output_image)


def list_files(directory):
    try:
        files = os.listdir(directory)
        file_list = [f for f in files if os.path.isfile(os.path.join(directory, f))]

        return file_list
    except FileNotFoundError:
        print(f"Error: The directory '{directory}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


##
# @brief WorkAround API to use instead of cv2.imread
# because an error occurs if file path include Japanese
#
# @param filename
# @param flags flags to pass for OpenCV
# @param dtype
#
# @return image file
def imread(filename, flags=cv2.IMREAD_COLOR, dtype=numpy.uint8):
    try:
        n = numpy.fromfile(filename, dtype)
        img = cv2.imdecode(n, flags)
        return img
    except Exception as e:
        print(e)
        return None


##
# @brief WorkAround API to use instead of cv2.imread
# because an fail to write if file path include Japanese
#
# @param filename
# @param img
# @param params
#
# @return 
def imwrite(filename, img, params=None):
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]
    directory_path = directory_path.encode('utf-8').decode('utf-8')
    file_list = list_files(directory_path)

    if file_list:
        for file in file_list:
            face_location(directory_path, file)
    else:
        print("No files found in the directory or an error occurred.")
