import os
import numpy
import cv2


##
# @brief make list of file names
#
# @param directory target directory
#
# @return file name list
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
# @brief Rename files in a directory to sequential file names
# Used to organize test data
#
# @param str target directory
# @param str tagname
#
# @return
def rename_files(dir_path: str, new_tag: str):
    file_list = list_files(dir_path)

    for index, filename in enumerate(file_list, start=1):
        (old_tag, ext) = os.path.splitext(filename)

        new_filename = new_tag + f"_{index}" + ext

        old_file_path = os.path.join(dir_path, filename)
        new_file_path = os.path.join(dir_path, new_filename)

        os.rename(old_file_path, new_file_path)
        print(f"Renamed {filename} to {new_filename}")


##
# @brief WorkAround API to use instead of cv2.imread
# because an error occurs if file path include Japanese
#
# @param filename
# @param flags flags to pass for OpenCV
# @param dtype
#
# @return image file
def cv2_imread(filename, flags=cv2.IMREAD_COLOR, dtype=numpy.uint8):
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
def cv2_imwrite(filename, img, params=None):
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
