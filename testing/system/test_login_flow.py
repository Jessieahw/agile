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


# def test_csrf_protected_save(driver, live_server):
#     register(driver, live_server, "csuser", "pw")
#     login(driver, live_server, "csuser", "pw")

#     driver.get(f"{live_server}/epl")
#     token = get_csrf_from_meta(driver)
#     assert token, "CSRF meta tag not found on /epl page"

#     status = driver.execute_async_script(
#         """
#         const done  = arguments[0];
#         const token = arguments[1];
#         fetch('/save_comparison', {
#             method: 'POST',
#             headers: {
#                 'Content-Type': 'application/json',
#                 'X-CSRFToken': token
#             },
#             body: JSON.stringify({
#                 avg_shots: 10,
#                 avg_goals: 1,
#                 avg_fouls: 1,
#                 avg_cards: 1,
#                 shot_accuracy: 0.9,
#                 matched_team: 'Test'
#             })
#         }).then(r => done(r.status)).catch(_ => done(-1));
#         """,
#         token,
#     )

#     assert status == 200

