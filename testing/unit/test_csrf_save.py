import json, server

def create_user_and_login(client, csrf):
    client.post("/register", data={
        "username": "u1", "password": "pw", "csrf_token": csrf
    })
    client.post("/login", data={
        "username": "u1", "password": "pw", "csrf_token": csrf
    })

def test_save_without_csrf(client):
    create_user_and_login(client, None)
    res = client.post("/save_comparison", json={})
    assert res.status_code == 400

def test_save_with_csrf(client, csrf_token):
    create_user_and_login(client, csrf_token)
    res = client.post("/save_comparison",
                      json={"avg_shots":10,"avg_goals":1.5,
                            "avg_fouls":1,"avg_cards":1.2,
                            "shot_accuracy":0.5,"matched_team":"Tottenheim"},
                      headers={"X-CSRFToken": csrf_token})
    assert res.status_code == 200
