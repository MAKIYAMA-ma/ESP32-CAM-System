# coding: UTF-8
import os
import sys
import itertools
import compare_face


def list_files_joined(directory):
    try:
        files = os.listdir(directory)
        file_list = [os.path.join(directory, f) for f in files if os.path.isfile(os.path.join(directory, f))]

        return file_list
    except FileNotFoundError:
        print(f"Error: The directory '{directory}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def main(dir_path1: str, dir_path2: str):
    file_list1 = list_files_joined(dir_path1)
    file_list2 = list_files_joined(dir_path2)

    pairs = [list(item) for item in list(itertools.product(file_list1, file_list2))]

    print(pairs)

    for p in pairs:
        sim = compare_face.get_sim(p[0], p[1])
        p.insert(0, sim)

    sorted_data = sorted(pairs, key=lambda x: x[0], reverse=True)

    for p in sorted_data:
        print(p)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <directory_path> <directory_path>")
        sys.exit(1)

    directory_path1 = sys.argv[1]
    directory_path2 = sys.argv[2]
    main(directory_path1, directory_path2)
