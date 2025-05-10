# nba.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from server import db            # import the SQLAlchemy() instance
from server import app           # to get at `app.logger` & `flash()`

nba_bp = Blueprint(
    'nba', 
    __name__, 
    template_folder='templates', 
    static_folder='static'
)

# ─── Model ────────────────────────────────────────────────────────────
class Submission(db.Model):
    __tablename__ = 'submissions'
    id     = db.Column(db.Integer, primary_key=True)
    wpct   = db.Column(db.Float,   nullable=False)
    pf     = db.Column(db.Float,   nullable=False)
    pa     = db.Column(db.Float,   nullable=False)
    result = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return (
            f"<Submission {self.id}: wpct={self.wpct}, "
            f"pf={self.pf}, pa={self.pa}, result={self.result}>"
        )

# Make sure the submissions table exists
with app.app_context():
    db.create_all()


# ─── Routes ────────────────────────────────────────────────────────────
@nba_bp.route('/')
def home():
    return render_template('index.html')


@nba_bp.route('/teams')
@nba_bp.route('/teams/<team_key>')
def teams(team_key=None):
    teams = {
                'ATL': 'Atlanta Hawks',
        'BOS': 'Boston Celtics',
        'BKN': 'Brooklyn Nets',
        'CHA': 'Charlotte Hornets',
        'CHI': 'Chicago Bulls',
        'CLE': 'Cleveland Cavaliers',
        'DAL': 'Dallas Mavericks',
        'DEN': 'Denver Nuggets',
        'DET': 'Detroit Pistons',
        'GS' : 'Golden State Warriors',
        'HOU': 'Houston Rockets',
        'IND': 'Indiana Pacers',
        'LAC': 'Los Angeles Clippers',
        'LAL': 'Los Angeles Lakers',
        'MEM': 'Memphis Grizzlies',
        'MIA': 'Miami Heat',
        'MIL': 'Milwaukee Bucks',
        'MIN': 'Minnesota Timberwolves',
        'NO': 'New Orleans Pelicans',  # or 'NO'
        'NY' : 'New York Knicks',
        'OKC': 'Oklahoma City Thunder',
        'ORL': 'Orlando Magic',
        'PHI': 'Philadelphia 76ers',
        'PHO': 'Pheonix Suns',
        'POR': 'Portland Trail Blazers',
        'SAC': 'Sacramento Kings',
        'SA' : 'San Antonio Spurs',
        'TOR': 'Toronto Raptors',
        'UTA': 'Utah Jazz',
        'WAS': 'Washington Wizards',
    }
    logos = {
        key: url_for('static', filename=f'nba_logos/{key}.png')
        for key in teams
    }
    return render_template(
        'teams.html',
        teams=teams,
        logos=logos,
        selected_team=team_key
    )


@nba_bp.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        wpct   = float(request.form.get('wpct', 0))
        pf     = float(request.form.get('pf',   0))
        pa     = float(request.form.get('pa',   0))
        result = request.form.get('result', 'Unknown')

        try:
            sub = Submission(wpct=wpct, pf=pf, pa=pa, result=result)
            db.session.add(sub)
            db.session.commit()
            app.logger.info(f"Saved submission {sub.id}")
            flash('Your team match has been saved!', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving submission: {e}")
            flash('There was an error saving your submission.', 'danger')

        return redirect(url_for('nba.data'))

    return render_template('data.html')