import json, server

def create_user_and_login(client, csrf):
    client.post("/register", data={
        "username":"u1", "password":"pw", "csrf_token":csrf
    }, follow_redirects=True)
    client.post("/login", data={
        "username":"u1", "password":"pw", "csrf_token":csrf
    }, follow_redirects=True)

# Save Comparison Tests
def test_save_comparison_without_csrf(client):
    create_user_and_login(client, None)
    res = client.post("/save_comparison", json={})
    assert res.status_code == 400

def test_save_comparison_with_csrf(client, csrf_token):
    create_user_and_login(client, csrf_token)
    res = client.post("/save_comparison",
                      json={"avg_shots":10,"avg_goals":1.5,
                            "avg_fouls":1,"avg_cards":1.2,
                            "shot_accuracy":0.5,"matched_team":"Tottenheim"},
                      headers={"X-CSRFToken": csrf_token})
    assert res.status_code == 200

def test_save_comparison_with_invalid_csrf(client, csrf_token):
    create_user_and_login(client, csrf_token)
    res = client.post("/save_comparison",
                      json={"avg_shots":10,"avg_goals":1.5,
                            "avg_fouls":1,"avg_cards":1.2,
                            "shot_accuracy":0.5,"matched_team":"Tottenheim"},
                      headers={"X-CSRFToken": "invalid_token"})
    assert res.status_code == 400

# BBL Similarity Search POST Tests:
def test_bbl_search_without_csrf(client):
    create_user_and_login(client, None)
    res = client.post("/bbl", json={
                                    "bat_innings": 100,
                                    "bat_runs": 2300,
                                    "bat_high": 120,
                                    "bat_avg": 23,
                                    "bat_sr": 130,
                                    "bowl_overs": 100,
                                    "bowl_wkts": 35,
                                    "bowl_runs": 700,
                                    "bowl_avg": 24,
                                    "bowl_eco": 7})
    assert res.status_code == 400

def test_bbl_search_with_csrf(client, csrf_token):
    create_user_and_login(client, csrf_token)
    res = client.post("/bbl",
                      json={
                        "bat_innings": 100,
                        "bat_runs": 2300,
                        "bat_high": 120,
                        "bat_avg": 23,
                        "bat_sr": 130,
                        "bowl_overs": 100,
                        "bowl_wkts": 35,
                        "bowl_runs": 700,
                        "bowl_avg": 24,
                        "bowl_eco": 7},
                      headers={"X-CSRFToken": csrf_token})
    assert res.status_code == 200

def test_bbl_search_with_invalid_csrf(client, csrf_token):
    create_user_and_login(client, csrf_token)
    res = client.post("/bbl",
                      json={
                        "bat_innings": 100,
                        "bat_runs": 2300,
                        "bat_high": 120,
                        "bat_avg": 23,
                        "bat_sr": 130,
                        "bowl_overs": 100,
                        "bowl_wkts": 35,
                        "bowl_runs": 700,
                        "bowl_avg": 24,
                        "bowl_eco": 7},
                      headers={"X-CSRFToken": "invalid_token"})
    assert res.status_code == 400

def test_registration_writes_user(client, csrf_token):
    # register
    client.post("/register", data={
        "username":"eve",
        "password":"pw",
        "csrf_token": csrf_token
    }, follow_redirects=True)

    # assert user exists in the test DB (not sports.db)
    from server import User, db
    assert User.query.filter_by(username="eve").count() == 1

def test_login_on_prior_registered_user(client, csrf_token):
    # login via prior test's registration
    res = client.post("/login", data={
        "username":"eve",
        "password":"pw",
        "csrf_token": csrf_token
    }, follow_redirects=True)

    assert res.status_code == 200

def test_no_login_user_using_bbl_player_search(client):
    PATH = "/bbl/player_search"
    player_name = "Chris".replace(" ", "%20")
    res = client.get(f"{PATH}?player_name={player_name}")
    assert res.status_code == 302 # Flask redirects to login page rather than rejecting via 401 Forbidden Errors.

def test_logged_user_using_bbl_player_search(client, csrf_token):
    # Fail safe registration if test run in isolation
    res = client.post("/register", data={
        "username":"eve",
        "password":"pw",
        "csrf_token": csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200

    # Login via prior test's registration
    res = client.post("/login", data={
        "username":"eve",
        "password":"pw",
        "csrf_token": csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    # We need to get session cookie to use in the next request
    PATH = "/bbl/player_search"
    player_name = "Chris".replace(" ", "%20")
    res = client.get(f"{PATH}?player_name={player_name}")
    assert res.status_code == 200 # Should return 200 OK

def test_no_login_user_using_bbl_team_search(client):
    PATH = "/bbl/player_search"
    team = "Chris".replace(" ", "%20")
    res = client.get(f"{PATH}?player_name={player_name}")
    assert res.status_code == 302 # Flask redirects to login page rather than rejecting via 401 Forbidden Errors.

def test_logged_user_using_bbl_team_search(client, csrf_token):
    # Fail safe registration if test run in isolation
    res = client.post("/register", data={
        "username":"eve",
        "password":"pw",
        "csrf_token": csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200

    # Login via prior test's registration
    res = client.post("/login", data={
        "username":"eve",
        "password":"pw",
        "csrf_token": csrf_token
    }, follow_redirects=True)
    assert res.status_code == 200
    # We need to get session cookie to use in the next request
    PATH = "/bbl/player_search"
    player_name = "Chris".replace(" ", "%20")
    res = client.get(f"{PATH}?player_name={player_name}")
    assert res.status_code == 200 # Should return 200 OK