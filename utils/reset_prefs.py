from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def reset_prefs(uname, pword):
    driver = webdriver.Chrome()
    try:
        driver.get('https://myadcenter.google.com/controls')

        username = driver.find_element(By.NAME, "identifier")
        username.send_keys(uname)  # username here
        driver.find_element(By.ID, "identifierNext").click()

        nextButton = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "passwordNext"))
        )
        password = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        password.send_keys(pword)  # password here
        driver.execute_script("arguments[0].click();", nextButton)

        my_ads = WebDriverWait(driver, 30).until(
                 EC.presence_of_element_located((By.XPATH, "/html/body/c-wiz/div/div[2]/gm-coplanar-drawer/div/div/div/ul/li[1]/span[3]/span"))
        )
        driver.execute_script("arguments[0].click();", my_ads)

        see_all_topics = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/c-wiz/div/div[2]/div/c-wiz/div/div[2]/c-wiz[1]/div/div[1]/div/div/a"))
        )
        driver.execute_script("arguments[0].click();", see_all_topics)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/c-wiz/div/div[2]/div/c-wiz/div/div[2]/div[2]/span/div/c-wiz/div/ul"))
        )
        element_list = driver.find_element(By.XPATH, "/html/body/c-wiz/div/div[2]/div/c-wiz/div/div[2]/div[2]/span/div/c-wiz/div/ul")
        items = element_list.find_elements(By.TAG_NAME, "li")

        f = open(uname + "_interests.txt", "a+")
        for item in items:
            text = item.text
            f.write(text + "\n")
        f.close()

        button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/c-wiz/div/div[2]/div/c-wiz/div/c-wiz/div/div/div[1]/c-wiz/div/gm3-tonal-button"))
        )
        driver.execute_script("arguments[0].click();", button)

        turn_off_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[8]/div[2]/div/div[2]/div[2]/div/gm3-text-button[2]/button/span[1]"))
        )
        driver.execute_script("arguments[0].click();", turn_off_button)

        got_it_button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[8]/div[2]/div/div[2]/gm3-text-button/button/span[1]"))
        )
        driver.execute_script("arguments[0].click();", got_it_button)
    except Exception as e:
        print("Exception ", e)
    finally:
        return driver


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    f = open("creds.txt", "r")
    lines = f.readlines()
    for line in lines:
        creds = line.split(",")
        driver = reset_prefs(creds[0], creds[1])
        driver.close()
