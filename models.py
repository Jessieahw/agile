from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Submission(db.Model):
    __tablename__ = 'submissions'
    id     = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    wpct   = db.Column(db.Float,   nullable=False)
    pf     = db.Column(db.Float,   nullable=False)
    pa     = db.Column(db.Float,   nullable=False)
    result = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return (
            f"<Submission {self.id}: wpct={self.wpct}, "
            f"pf={self.pf}, pa={self.pa}, result={self.result}>"
        )
    
    user = db.relationship('User', backref='submissions')
    
class PlayerComparison(db.Model):
    __tablename__ = 'player_comparisons'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    input_pts = db.Column(db.Float)
    input_ast = db.Column(db.Float)
    input_stl = db.Column(db.Float)
    
    input_blk = db.Column(db.Float)
    input_trb = db.Column(db.Float)
    matched_player = db.Column(db.String(100))

    user = db.relationship('User', backref='player_comparisons')
