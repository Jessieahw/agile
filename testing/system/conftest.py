import threading, pytest, time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import server                                # imports the same global app

@pytest.fixture(scope="session")
def live_server():
    def run():
        server.app.run(port=5001, use_reloader=False)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(1)            # give Flask a second to boot
    yield "http://localhost:5001"

@pytest.fixture(scope="session")
def driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
    yield driver
    driver.quit()
