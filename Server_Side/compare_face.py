import insightface
import numpy
import sys
import cv2
import util
import os


class Comparator:
    face_analysis = None
    regface_emeddings = []

    def __init__(self):
        self.face_analysis = insightface.app.FaceAnalysis()
        self.face_analysis.prepare(ctx_id=0, det_size=(640, 640))

    def save_regfaces(self):
        regface_dir = "./register"
        regfaces = util.list_files(regface_dir)
        regface_full_paths = [os.path.join(regface_dir, face) for face in regfaces]

        for p in regface_full_paths:
            self.regface_emeddings = self.regface_emeddings + self.calc_emedding(p)

        print(self.regface_emeddings)

    def get_reg_sim(self, img: str):
        target_embeddings = self.calc_emedding(img)

        results = []
        for t in target_embeddings:
            target_results = []
            for r in self.regface_emeddings:
                target_results.append(self.compute_sim(t, r))
            results.append(target_results)

        return results

    # REF: https://github.com/deepinsight/insightface/blob/f474870cc5b124749d482cf175818413a9fe12cd/python-package/insightface/model_zoo/arcface_onnx.py#L70
    def calc_emedding(self, img: str):
        image = util.cv2_imread(img, cv2.IMREAD_UNCHANGED)
        faces = self.face_analysis.get(image)
        embeddings = []
        if len(faces) == 0:
            print("face is not detected from " + img)
        for f in faces:
            embeddings.append(f.embedding)

        return embeddings

    def compute_sim(self, feat1, feat2):
        return numpy.dot(feat1, feat2) / (numpy.linalg.norm(feat1) * numpy.linalg.norm(feat2))

    def get_sim(self, img1: str, img2: str):
        tmp = self.calc_emedding(img1)
        if tmp is not None:
            embedding1 = self.calc_emedding(img1)[0]
        else:
            return None

        tmp = self.calc_emedding(img2)
        if tmp is not None:
            embedding2 = self.calc_emedding(img2)[0]
        else:
            return None

        return self.compute_sim(embedding1, embedding2)

    def main(self, img1: str, img2: str):
        print("[" + img1 + " x " + img2 + "]:" + str(self.get_sim(img1, img2)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_face.py <image1 path> <image2 path>")
        sys.exit(1)

    image1 = sys.argv[1]
    image2 = sys.argv[2]

    comparator = Comparator()

    comparator.main(image1, image2)
