import os, tempfile, pytest
import server                               # ← imports the real app object
from server import db

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
    html = client.get("/login").data.decode()
    start = html.find('name="csrf_token" value="') + 24
    return html[start:html.find('"', start)]
