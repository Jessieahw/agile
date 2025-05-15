"""
System-test fixtures
– Spins up a live Flask server on port 5001
– Provides a headless-Chrome WebDriver managed by Selenium 4
   (no webdriver_manager needed)
"""
import threading, time, pytest, tempfile, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from server import create_app, db  # if you're using SQLAlchemy like db = SQLAlchemy(app)

@pytest.fixture(scope="session")
def live_server():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": True,
    })

    with app.app_context():
        db.create_all()

    threading.Thread(
        target=lambda: app.run(port=5001, use_reloader=False, debug=True),
        daemon=True
    ).start()
    time.sleep(1)
    yield "http://localhost:5001"

    os.close(db_fd)
    os.unlink(db_path)


# ----------------------------------------------------------------------
# Headless Chrome driver (Selenium Manager handles the driver binary)
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def driver():
    opts = Options()
    # opts.add_argument("--headless=new")    # Chrome > 109 headless mode
    drv = webdriver.Chrome(options=opts)   # Selenium downloads driver
    drv.implicitly_wait(3)
    yield drv
    drv.quit()
