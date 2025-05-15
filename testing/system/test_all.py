from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

# ---------- helper utilities ----------

def _grab_csrf_token(driver, base):
    """Open /login once and pull the hidden WTForms token so we can reuse it."""
    driver.get(f"{base}/login")
    return driver.find_element(By.NAME, "csrf_token").get_attribute("value")


def register(driver, base, user, pw):
    driver.get(f"{base}/register")

    # token already correct – just read it if you later want to inspect
    # token = driver.find_element(By.NAME, "csrf_token").get_attribute("value")

    driver.find_element(By.NAME, "username").send_keys(user)
    driver.find_element(By.NAME, "password").send_keys(pw)
    WebDriverWait(driver, 3)
    driver.find_element(By.CLASS_NAME, "form-button").click()

    # Wait until we’re redirected away from /register (302 → /login)
    WebDriverWait(driver, 5).until(
        lambda d: "/register" not in d.current_url
    )


def login(driver, base, user, pw):
    """Log the user in (page already contains a valid CSRF hidden field)."""
    driver.get(f"{base}/login")
    driver.find_element(By.NAME, "username").send_keys(user)
    driver.find_element(By.NAME, "password").send_keys(pw)
    driver.find_element(By.CLASS_NAME, "form-button").click()
    WebDriverWait(driver, 1)
    print(f"After login: {driver.current_url}")
    WebDriverWait(driver, 5).until(lambda d: "/login" not in d.current_url)


def get_csrf_from_meta(driver):
    return driver.execute_script(
        "return document.querySelector(\"meta[name='csrf-token']\")?.content;"
    )

# ---------- actual tests ----------

def test_redirect_when_not_logged_in(driver, live_server):
    driver.get(f"{live_server}/epl")
    assert "/login" in driver.current_url


def test_register_login_logout_flow(driver, live_server):
    register(driver, live_server, "u1", "pw")
    login(driver, live_server, "u1", "pw")

    # landing page should be reached after successful login
    assert driver.current_url.rstrip("/") == live_server

    driver.get(f"{live_server}/logout")
    assert "/login" in driver.current_url


def test_bbl_submission_with_csrf(driver, live_server):
    register(driver, live_server, "bbluser", "pw")
    login(driver, live_server, "bbluser", "pw")

    driver.get(f"{live_server}/bbl")
    WebDriverWait(driver, 3)
    token = get_csrf_from_meta(driver)
    # Check the CSRF token in the meta tag
    assert token != "", "CSRF meta tag not found on /bbl page"

    # Fill in batting stats
    driver.find_element(By.NAME, "bat_innings").send_keys("100")
    driver.find_element(By.NAME, "bat_runs").send_keys("2300")
    driver.find_element(By.NAME, "bat_high").send_keys("120")
    driver.find_element(By.NAME, "bat_avg").send_keys("23")
    driver.find_element(By.NAME, "bat_sr").send_keys("130")

    # Fill in bowling stats
    driver.find_element(By.NAME, "bowl_overs").send_keys("100")
    driver.find_element(By.NAME, "bowl_wkts").send_keys("34")
    driver.find_element(By.NAME, "bowl_runs").send_keys("700")
    driver.find_element(By.NAME, "bowl_avg").send_keys("20")
    driver.find_element(By.NAME, "bowl_eco").send_keys("7.0")

    # Submit the form
    driver.find_element(By.CLASS_NAME, "submit-btn").click()
    # Wait for the page to load after submission
    WebDriverWait(driver, 3)

    # Get the table data
    table = driver.find_element(By.CLASS_NAME, "similar-table")
    assert table, "Table not found on the page"

    # Check if the table contains the submitted data by simple check for names in the table source
    table_source = table.get_attribute("innerHTML")
    assert "Alex Hales" in table_source, "Table does not contain or is not the correct result of the submitted batting data!"
    assert "Josh Philippe" in table_source, "Table does not contain or is not the correct result of the submitted bowling data!"
    assert "Daniel Hughes" in table_source, "Table does not contain or is not the correct result of the submitted bowling data!"



def test_epl_recommended_team_search(driver, live_server):
    register(driver, live_server, "csuser", "pw")
    login(driver, live_server, "csuser", "pw")

    driver.get(f"{live_server}/epl")
    token = get_csrf_from_meta(driver)
    # Check the CSRF token in the meta tag
    assert token, "CSRF meta tag not found on /epl page"

    driver.find_element(By.NAME, "avgShots").send_keys("10")
    driver.find_element(By.NAME, "avgGoals").send_keys("1.5")
    driver.find_element(By.NAME, "avgFouls").send_keys("8")
    driver.find_element(By.NAME, "avgCards").send_keys("1.2")
    driver.find_element(By.NAME, "shotAccuracy").send_keys("0.5" + Keys.RETURN)
    driver.find_element(By.XPATH, "//button[text()='Find Your EPL Team']").click()
    WebDriverWait(driver, 3)
    # Get the recommended team:
    team = driver.find_element(By.ID, "modalText").text
    assert team != "", "No recommended team found in the modal!"
    assert "tottenham" in team.lower(), "The recommended team is not Tottenham Hotspur!"


