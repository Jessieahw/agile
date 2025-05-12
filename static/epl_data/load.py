import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import csv
from server import app, db, Team  # Import the app, db, and Team model from server.py
def load_csv_to_database():
    # Path to your CSV file
    csv_file_path = 'team_comparison_stats.csv'

    # Use the Flask app context to access the database
    with app.app_context():
        # Open the CSV file and read its contents
        with open(csv_file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)

            # Iterate through each row in the CSV
            for row in reader:
                # Check if the team already exists in the database
                if not Team.query.filter_by(name=row['Team']).first():
                    # Create a new Team object
                    team = Team(
                        name=row['Team'],  # Match the 'Team' column
                        avg_shots=float(row['Average Shots per Match']),
                        avg_goals=float(row['Average Goals per Match']),
                        avg_fouls=float(row['Average Fouls per Match']),
                        avg_cards=float(row['Average Cards per Match']),
                        shot_accuracy=float(row['Shot Accuracy'])
                    )
                    # Add the team to the database session
                    db.session.add(team)

        # Commit the session to save the data
        db.session.commit()
        print("CSV data loaded into the database successfully!")

if __name__ == '__main__':
    # Create the database tables if they don't exist
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Tables created successfully.")

    # Load data from CSV into the database
    load_csv_to_database()