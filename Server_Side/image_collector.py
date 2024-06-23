import time
import sys
import os
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys


##
# @brief Google image search
#
# @param str searching key
#
# @return result
def google_search_result(key: str, num: int):
    try:
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')

        driver = webdriver.Edge(options=options)
        # Google Image Search
        # print(f'https://www.google.com/search?tbm=isch&q={key}')
        driver.get(f'https://www.google.com/search?tbm=isch&q={key}')

        # wait for finish
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search'))
        )

        # for debug (to check result)
        # time.sleep(10)

        # get img list
        # img_elements = driver.find_elements(By.TAG_NAME, 'img')

        # make output dir
        output_dir = 'result\\' + key
        os.makedirs(output_dir, exist_ok=True)

        last_height = driver.execute_script("return document.body.scrollHeight")
        img_cnt = 1
        seen_srcs = set()

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # 新しい高さを計測
            new_height = driver.execute_script("return document.body.scrollHeight")

            # get img list
            img_elements = driver.find_elements(By.TAG_NAME, 'img')
            print(len(img_elements))

            # imgタグごとに処理
            idx = 0
            for index, img_element in enumerate(img_elements):
                # src属性を取得
                img_src = img_element.get_attribute('src')
                if img_src is None:
                    print("None" + str(idx))
                    idx = idx+1
                    continue
                if img_src in seen_srcs:
                    print("Known" + str(idx))
                    idx = idx+1
                    continue

                # src属性がBase64形式か確認
                print(img_src)
                # if img_src and img_src.startswith('data:image/jpeg;base64,'):
                if img_src and img_src.startswith('data:image/'):
                    # Base64部分を抽出
                    base64_data = img_src.split(',')[1]
                    img_format = img_src.split(';')[0].split('/')[1]

                    # Base64デコード
                    img_data = base64.b64decode(base64_data)

                    # 画像を保存
                    file_path = os.path.join(output_dir, f'image_{img_cnt}.{img_format}')
                    seen_srcs.add(img_src)
                    img_cnt = img_cnt + 1
                    with open(file_path, 'wb') as file:
                        file.write(img_data)

                    print(f'Saved {file_path}')
                # else:
                #     print(f'Skipped img tag {img_cnt}, src attribute is not in Base64 format.')

            # スクロール終了条件を確認
            if new_height == last_height:
                break
            if img_cnt > num:
                break
            last_height = new_height
    finally:
        # ブラウザを閉じる (エラーが発生しても必ず実行)
        driver.quit()


if __name__ == '__main__':
    args = sys.argv
    key = "ムロツヨシ"
    num = 100

    if 2 <= len(args):
        key = args[1]
    if 3 <= len(args):
        num = int(args[2])

    google_search_result(key, num)
