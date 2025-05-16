from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions

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


def test_bbl_similarity_search_submission_with_csrf(driver, live_server):
    register(driver, live_server, "bbluser0", "pw")
    login(driver, live_server, "bbluser0", "pw")

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

def test_bbl_player_search(driver, live_server):
    # Build up the user account and get authenticated.
    register(driver, live_server, "bbluser1", "pw")
    login(driver, live_server, "bbluser1", "pw")

    # Get to the page
    driver.get(f"{live_server}/bbl")

    # Wait for the nav button to appear, then click it
    WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_element_located((By.ID, "playersbtn"))
    )
    playersbtn = driver.find_element(By.ID, "playersbtn")
    playersbtn.click()

    # Wait for the search box to appear
    WebDriverWait(driver, 5).until(
        expected_conditions.visibility_of_element_located((By.ID, "player-search-input"))
    )

    # No token needed for this page (not a form). Just enter a player name
    player_name = "Chris"
    player_input = driver.find_element(By.ID, "player-search-input")
    player_input.send_keys(player_name)
    # Submit and wait for the result table to appear and fill out
    input_button = driver.find_element(By.ID, "player-search-btn")
    input_button.click()
    WebDriverWait(driver, 3).until(
        expected_conditions.visibility_of_element_located((By.CLASS_NAME, "similar-table"))
    )
    # Get the table data
    table = driver.find_element(By.CLASS_NAME, "similar-table")
    assert table, "Table not found on the page"

    # Parse the table
    rows = table.find_elements(By.TAG_NAME, "tr")
    data: set[tuple[str, str]] = set([])
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "th") or row.find_elements(By.TAG_NAME, "td")
        data.add(tuple(cell.text.strip() for cell in cells))

    # Set expected row data:
    expected_rows: set[tuple[str,str]] = {
        ("#", "Name", "Inn", "Runs", "HS", "Avg", "SR", "Wkts", "BAvg", "Eco"),
        ("1", "Chris Lynn", "113", "3632", "101", "32.14", "132.55", "3", "25.00", "6.82"),
        ("2", "Daniel Christian", "119", "1917", "73", "16.11", "117.34", "92", "27.02", "8.33"),
        ("4", "Chris Gayle", "20", "645", "100", "32.25", "125.48", "6", "30.50", "7.04")
    }

    # Print the table data for debugging
    print(f"Expected: {expected_rows}.\nActual: {data}\nDifference: {expected_rows.difference(data)}")
    assert expected_rows.issubset(data), "The table does not contain the expected data!"

def test_bbl_team_select(driver, live_server):
    # Build up the user account and get authenticated.
    register(driver, live_server, "bbluser2", "pw")
    login(driver, live_server, "bbluser2", "pw")

    # Get to the page
    driver.get(f"{live_server}/bbl")

    # Wait for the nav button to appear, then click it
    WebDriverWait(driver, 1).until(
        expected_conditions.presence_of_element_located((By.ID, "teamsbtn"))
    )
    playersbtn = driver.find_element(By.ID, "teamsbtn")
    playersbtn.click()

    # Wait for the search selection box to appear
    WebDriverWait(driver, 1).until(
        expected_conditions.visibility_of_element_located((By.ID, "team‑select"))
    )
    # No token needed for this page (not a form). Just select the Perth Scorchers option
    select_element = driver.find_element(By.ID, "team‑select")
    sel = Select(select_element)
    sel.select_by_visible_text("PERTH SCORCHERS")
    
    # Wait for the table to appear
    WebDriverWait(driver, 0.5).until(
        expected_conditions.visibility_of_element_located((By.CLASS_NAME, "team‑table"))
    )
    # Get the table data
    table = driver.find_element(By.CLASS_NAME, "team‑table")
    assert table, "Table not found on the page"

    # Parse the table
    rows = table.find_elements(By.TAG_NAME, "tr")
    data: set[tuple[str, str]] = set([])
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
        data.add(tuple(cell.text.strip() for cell in cells))

    # Set expected row data:
    expected_rows: set[tuple[str,str]] = {
        ("Matches", "158"),
        ("Wins", "94"),
        ("Losses", "64"),
        ("Win %", "59.49"),
        ("Favoured opponent", "MELBOURNE RENEGADES (16 wins)"),
        ("Toughest opponent", "SYDNEY SIXERS (13 losses)"),
        ("Seasons won", "2013-2014, 2014-2015, 2016-2017, 2021-2022, 2022-2023")
    }

    # Print the table data for debugging
    print(f"Expected: {expected_rows}.\nActual: {data}\nDifference: {expected_rows.difference(data)}")
    assert expected_rows.issubset(data), "The table does not contain the expected data!"


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
    WebDriverWait(driver, 3)
    driver.find_element(By.CLASS_NAME, "close").click() # Close the modal text popup
    WebDriverWait(driver, 3)
    assert team != "", "No recommended team found in the modal!"
    assert "tottenham" in team.lower(), "The recommended team is not Tottenham Hotspur!"

def test_nba_team_search(driver, live_server):
    register(driver, live_server, "nbauser0", "pw")
    login(driver, live_server, "nbauser0", "pw")

    driver.get(f"{live_server}/nba")
    # token = get_csrf_from_meta(driver)
    # # Check the CSRF token in the meta tag
    # assert token, "CSRF meta tag not found on /nba page"

    select_element = driver.find_element(By.CLASS_NAME, "form-select")
    select_element.click()
    sel = Select(select_element)
    sel.select_by_visible_text("Boston Celtics (BOS)")
    # Close the box:
    select_element = driver.find_element(By.CLASS_NAME, "form-select")
    select_element.click()
    WebDriverWait(driver, 1).until(
        expected_conditions.text_to_be_present_in_element((By.CLASS_NAME, "table"), "Boston Celtics (BOS)")
    )
    # Parse the table
    table =driver.find_element(By.CLASS_NAME, "stats-table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    data: set[tuple[str, str]] = set([])
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "th") or row.find_elements(By.TAG_NAME, "td")
        data.add(tuple(cell.text.strip() for cell in cells))

    # Set expected row data:
    expected_rows: set[tuple[str,str]] = {
        ("Season", "2025"),
        ("Team", "Boston Celtics (BOS)"),
        ("Conference", "Eastern"),
        ("Division", "Atlantic")
    }
    print(f"Data: {data}")
    assert expected_rows.issubset(data), "The table does not contain the expected data!"

def test_nba_team_match(driver, live_server):
    register(driver, live_server, "nbauser1", "pw")
    login(driver, live_server, "nbauser1", "pw")

    driver.get(f"{live_server}/nba/data.html")

    # Get the CSRF token from the form
    token = driver.find_element(By.NAME, "csrf_token").get_attribute("value")
    assert token, "CSRF token not found in form on /nba/data.html"

    # Fill in the form fields
    driver.find_element(By.ID, "wpct").send_keys("50")
    driver.find_element(By.ID, "pf").send_keys("107")
    driver.find_element(By.ID, "pa").send_keys("103")

    # Submit the form
    driver.find_element(By.ID, "submit").click()

    # Wait for the modal content to be visible
    WebDriverWait(driver, 10).until(
        expected_conditions.visibility_of_element_located((By.ID, "modalBody"))
    )

    # Read the modal content and verify expected team appears
    modal_text = driver.find_element(By.ID, "modalBody").text
    print("Modal loaded text:", modal_text)
    assert "Orlando Magic (ORL)" in modal_text, f"Unexpected modal content: {modal_text}"


def test_nba_player_match(driver, live_server):
    register(driver, live_server, "nbauser2", "pw")
    login(driver, live_server, "nbauser2", "pw")
    # Get to the page and grab the CSRF token
    driver.get(f"{live_server}/nba/player.html")
    token  = driver.find_element(By.NAME, "csrf_token").get_attribute("value")
    assert token, "CSRF meta tag not found on /nba page"

    # Now fill in the form:
    points = driver.find_element(By.ID, "pts")
    points.send_keys("30")
    assists = driver.find_element(By.ID, "ast")
    assists.send_keys("3")
    steals = driver.find_element(By.ID, "stl")
    steals.send_keys("0")
    blocks = driver.find_element(By.ID, "blk")
    blocks.send_keys("10")
    rebounds = driver.find_element(By.ID, "trb")
    rebounds.send_keys("7")
    submit = driver.find_element(By.CLASS_NAME, "btn-primary")
    submit.click()
    # Wait for the modal to appear
    WebDriverWait(driver, 5).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "resultModalLabel"), "You vs. Victor Wembanyama"
        )
    )
    # Get the table data
    table = driver.find_element(By.CLASS_NAME, "table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    data: set[tuple[str, str]] = set([])
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
        data.add(tuple(cell.text.strip() for cell in cells))

    # Set expected row data:
    expected_rows: set[tuple[str,str]] = {
        ("Stat", "You", "Victor Wembanyama"),
        ("Points", "30", "30"),
        ("Assists", "3", "3"),
        ("Steals", "0", "0"),
        ("Blocks", "10", "10"),
        ("Rebounds", "7", "7")
    }
    print(f"Expected: {expected_rows}.\nActual: {data}")
    assert expected_rows.issubset(data), "The table does not contain the expected data!"

def test_nba_team_standings(driver, live_server):
    register(driver, live_server, "nbauser3", "pw")
    login(driver, live_server, "nbauser3", "pw")
    # Get to the page and grab the CSRF token
    driver.get(f"{live_server}/nba/")
    # No CSRF token needed for this page (not a form)

    # Now quantify the selected team:
    select_element = driver.find_element(By.CLASS_NAME, "form-select")
    sel = Select(select_element)
    sel.select_by_visible_text("New York Knicks (NY)")
    # Close the box:
    select_element = driver.find_element(By.CLASS_NAME, "form-select")
    select_element.click()
    # Wait for the table to load
    WebDriverWait(driver, 5).until(
        expected_conditions.text_to_be_present_in_element(
            (By.CLASS_NAME, "table"), "New York Knicks (NY)"
        )
    )
    print(f"Current Table Text: {driver.find_element(By.CLASS_NAME, 'table').text}")

    

