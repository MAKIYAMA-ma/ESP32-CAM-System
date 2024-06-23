import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys


##
# @brief Google image search
#
# @param str searching key
#
# @return result
def google_search_result(key: str):
    try:
        driver = webdriver.Edge()
        # Google Image Search
        driver.get("https://www.google.co.jp/imghp?hl=ja")

        # Try Search
        search_box = driver.find_element(By.CLASS_NAME, 'gLFyf')
        search_box.send_keys(key)
        search_box.send_keys(Keys.RETURN)

        # wait for finish
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search'))
        )

        # for debug (to check result)
        time.sleep(10)
    finally:
        # ブラウザを閉じる (エラーが発生しても必ず実行)
        driver.quit()


def main():
    google_search_result("ムロツヨシ")


if __name__ == '__main__':
    main()
