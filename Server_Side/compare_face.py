import insightface
import numpy
import sys
import cv2
import util


# REF: https://github.com/deepinsight/insightface/blob/f474870cc5b124749d482cf175818413a9fe12cd/python-package/insightface/model_zoo/arcface_onnx.py#L70
def compute_sim(feat1, feat2):
    return numpy.dot(feat1, feat2) / (numpy.linalg.norm(feat1) * numpy.linalg.norm(feat2))


def get_sim_with_fa(face_analysis, img1: str, img2: str):
    image1 = util.cv2_imread(img1, cv2.IMREAD_UNCHANGED)
    faces1 = face_analysis.get(image1)
    if len(faces1) == 0:
        print("face is not detected from " + img1)
        return
    embedding1 = faces1[0].embedding

    image2 = util.cv2_imread(img2, cv2.IMREAD_UNCHANGED)
    faces2 = face_analysis.get(image2)
    if len(faces2) == 0:
        print("face is not detected from " + img2)
        return
    embedding2 = faces2[0].embedding

    return compute_sim(embedding1, embedding2)


def create_face_analysis():
    face_analysis = insightface.app.FaceAnalysis()
    face_analysis.prepare(ctx_id=0, det_size=(640, 640))

    return face_analysis


def get_sim(img1: str, img2: str):
    return get_sim_with_fa(create_face_analysis(), img1, img2)


def main(img1: str, img2: str):
    print("[" + img1 + " x " + img2 + "]:" + str(get_sim(img1, img2)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <image1 path> <image2 path>")
        sys.exit(1)

    image1 = sys.argv[1]
    image2 = sys.argv[2]

    main(image1, image2)
