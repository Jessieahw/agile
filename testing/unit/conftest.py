import os, tempfile, pytest
import server                               # ← imports the real app object
from extensions import db
import re

@pytest.fixture()
def app():
    # point the *existing* app at an in‑memory DB
    server.app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": True,
        "SERVER_NAME": "localhost.localdomain"
    })
    with server.app.app_context():
        db.create_all()
        yield server.app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def csrf_token(client):
    # hit any page with a form; /login is quick
    html = client.get("/login").data.decode()
    # robust regex for value=""
    m = re.search(r'name="csrf_token".*?value="([^"]+)"', html, re.S)
    assert m, "CSRF token not found in HTML"
    return m.group(1)
