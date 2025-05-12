import os
from math import sqrt
from sqlalchemy import (create_engine, Column, Integer, String, Float, ForeignKey, func, null)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

#  ORM setup 
Base = declarative_base()

class BBLPlayer(Base):
    __tablename__ = 'BBL_Players'
    player_id   = Column(Integer, primary_key=True)
    player_name = Column(String)

class BBLBattingInnings(Base):
    __tablename__ = 'BBL_BattingInnings'
    id        = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('BBL_Players.player_id'))
    runs      = Column(Integer)
    balls     = Column(Integer)

    player = relationship('BBLPlayer', backref='batting_innings')

class BBLBowlingInnings(Base):
    __tablename__ = 'BBL_BowlingInnings'
    id        = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('BBL_Players.player_id'))
    overs     = Column(Float)          # stored as decimal overs (e.g. 10.4)
    wickets   = Column(Integer)
    runs      = Column(Integer)
    economy   = Column(Float)

    player = relationship('BBLPlayer', backref='bowling_innings')

# Single engine / session factory for the module
DB_PATH = os.path.join(os.path.dirname(__file__),
                        'static', 'bbl', 'data', 'data.db')
DB_ENGINE  = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=DB_ENGINE, autoflush=False, autocommit=False)

#  Similarity helpers 
def _euclidean_distance(*diffs) -> float:
    """Return √(Σ diff²)"""
    return sqrt(sum(d ** 2 for d in diffs))

#  Main matching API 
class BBLBestMatchFunctions:
    """
    Re‑implementation of the old hand‑written SQL using SQLAlchemy ORM.
    The `conn` parameter is accepted (for legacy calls) but ignored.
    """

    @classmethod
    def get_top_batters(cls, _conn, user_stats):
        session = SessionLocal()

        # Aggregate the five stats we need for each player
        players = (
            session.query(
                BBLPlayer.player_name.label('player_name'),

                # use COUNT(*) instead of COUNT(id)
                func.count().label('innings'),

                func.sum(BBLBattingInnings.runs).label('total_runs'),
                func.max(BBLBattingInnings.runs).label('high_score'),
                (func.sum(BBLBattingInnings.runs).cast(Float) /
                func.count()).label('batting_average'),
                func.avg(
                    BBLBattingInnings.runs * 100.0 /
                    func.nullif(BBLBattingInnings.balls, 0)
                ).label('strike_rate')
            )
            .join(BBLBattingInnings,
                BBLPlayer.player_id == BBLBattingInnings.player_id)
            .group_by(BBLPlayer.player_id)
            .having(func.count() > 5)          # ← same COUNT(*)
            .all()
        )

        # Compute similarity & return top‑10
        scored = []
        for row in players:
            dist = _euclidean_distance(
                user_stats['bat_innings'] - row.innings,
                user_stats['bat_runs']    - row.total_runs,
                user_stats['bat_high']    - row.high_score,
                user_stats['bat_avg']     - row.batting_average,
                user_stats['bat_sr']      - row.strike_rate
            )
            scored.append({
                'name':       row.player_name,
                'innings':    row.innings,
                'runs':       row.total_runs,
                'high_score': row.high_score,
                'bat_avg':    row.batting_average,
                'bat_sr':     row.strike_rate,
                'similarity': 1000 - dist
            })

        session.close()
        scored.sort(key=lambda r: -r['similarity'])
        return scored[:10]

    @classmethod
    def get_top_bowlers(cls, _conn, user_stats):
        session = SessionLocal()

        players = (
            session.query(
                BBLPlayer.player_name.label('player_name'),

                func.sum(BBLBowlingInnings.overs).label('overs'),
                func.sum(BBLBowlingInnings.wickets).label('wickets'),
                func.sum(BBLBowlingInnings.runs).label('runs_conceded'),

                (func.sum(BBLBowlingInnings.runs).cast(Float) /
                func.nullif(func.sum(BBLBowlingInnings.wickets), 0)
                ).label('bowling_average'),
                (func.sum(BBLBowlingInnings.runs).cast(Float) /
                func.nullif(func.sum(BBLBowlingInnings.overs), 0)
                ).label('economy_rate')
            )
            .join(BBLBowlingInnings,
                BBLPlayer.player_id == BBLBowlingInnings.player_id)
            .group_by(BBLPlayer.player_id)
            .having(func.count() > 5)          # ← COUNT(*) again
            .all()
        )

        scored = []
        for row in players:
            dist = _euclidean_distance(
                user_stats['bowl_overs'] - row.overs,
                user_stats['bowl_wkts']  - row.wickets,
                user_stats['bowl_runs']  - row.runs_conceded,
                user_stats['bowl_avg']   - row.bowling_average,
                user_stats['bowl_eco']   - row.economy_rate
            )
            scored.append({
                'name':          row.player_name,
                'overs':         row.overs,
                'wickets':       row.wickets,
                'runs_conceded': row.runs_conceded,
                'bowl_avg':      row.bowling_average,
                'eco':           row.economy_rate,
                'similarity':    1000 - dist
            })

        session.close()
        scored.sort(key=lambda r: -r['similarity'])
        return scored[:10]
