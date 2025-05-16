# Pro Player Comparison Web App

This web application allows users to compare their sports stats with professional athletes across multiple leagues, including the English Premier League (EPL), Australian Football League (AFL), National Basketball Association (NBA), and Big Bash League (BBL). Users can discover which pro player they are most similar to, visualize their stats, and share results publicly or privately with other users.

## Features

- **Stat Comparison:** Enter your stats and find the closest matching professional player in EPL, AFL, NBA, or BBL.
- **Data Visualization:** View your stats and matched player/team stats in interactive charts.
- **Forum Posting:** Share your results publicly to the forum.
- **Private Messaging:** Share your results privately with another registered user.
- **Post Management:** View all posts, received private messages (PMs), and sent PMs.
- **User Authentication:** Secure login and logout functionality.

## Getting Started

### Installation

1. **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd agile\ group\ project
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database:**
    ```bash
    flask db upgrade
    ```

5. **Run the application:**
    ```bash
    flask run
    ```

6. **Access the app:**
    Open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

- **Compare Stats:** Choose a league from the home page, enter your stats, and see which pro you match with.
- **Share Results:** Use the "Share to Forum" button to post publicly, or enter a username and click "Share Privately" to send a private message.
- **View Posts:** Use the navigation bar to view all posts, received PMs, or sent PMs.

## Project Structure

```
agile group project/
│
├── agile/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/
│   ├── templates/
│   │   ├── index.html
│   │   ├── epl.html
│   │   ├── afl.html
│   │   ├── nba.html
│   │   └── bbl.html
│   ├── server.py
│   └── ...
├── migrations/
│   └── ...
├── requirements.txt
└── README.md
```

## Notes

- Make sure to run database migrations if you change the models.
- Static assets (logos, icons) are in `static/assets/`.
- For development, debug mode can be enabled by setting `FLASK_ENV=development`.
