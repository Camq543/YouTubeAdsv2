from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def reset_prefs():
    driver = webdriver.Chrome()
    try:
        driver.get(
            'https://accounts.google.com/ServiceLogin?service=accountsettings&hl=en&continue=https://myaccount.google.com/intro/data-and-privacy')
        username = driver.find_element(By.NAME, "identifier")
        username.send_keys('') #username here
        driver.find_element(By.ID, "identifierNext").click()

        nextButton = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "passwordNext"))
        )
        password = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        password.send_keys("") #password here
        driver.execute_script("arguments[0].click();", nextButton)

    except Exception as e:
        print("Exception ", e)
    finally:
        return driver

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    driver = reset_prefs()
