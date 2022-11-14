from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def reset_prefs():
    driver = webdriver.Chrome()
    try:
        driver.get('https://myadcenter.google.com/controls')

        username = driver.find_element(By.NAME, "identifier")
        username.send_keys("")  # username here
        driver.find_element(By.ID, "identifierNext").click()

        nextButton = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "passwordNext"))
        )
        password = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        password.send_keys("")  # password here
        driver.execute_script("arguments[0].click();", nextButton)

        button = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/c-wiz/div/div[2]/div/c-wiz/div/c-wiz/div/div/div[1]/c-wiz/div/gm3-tonal-button"))
        )
        driver.execute_script("arguments[0].click();", button)

        turnOffButton = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[7]/div[2]/div/div[2]/div[2]/div/gm3-text-button[2]/button/span[1]"))
        )
        driver.execute_script("arguments[0].click();", turnOffButton)

        gotItButton = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[7]/div[2]/div/div[2]/gm3-text-button/button/span[1]"))
        )
        driver.execute_script("arguments[0].click();", gotItButton)
    except Exception as e:
        print("Exception ", e)
    finally:
        return driver


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    driver = reset_prefs()
