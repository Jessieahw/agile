class BBLBestMatchFunctions:
    # BBL PAGE SECTION:
    @classmethod
    def get_top_batters(cls, conn, user_stats):
        cur = conn.cursor()
        cur.execute("""
            SELECT p.player_name,
                AVG(b.runs) AS avg_runs,
                MAX(b.runs) AS high_score,
                AVG(b.runs * 1.0 / NULLIF(b.balls,0)) AS avg_strike_rate,
                AVG(b.runs) * 1.0 / COUNT(*) AS avg_bat_avg
            FROM BBL_Players p
            JOIN BBL_BattingInnings b ON p.player_id = b.player_id
            GROUP BY p.player_id
            HAVING COUNT(*) > 5
        """)
        players = cur.fetchall()
        results = []
        for row in players:
            dist = (
                (user_stats['bat_runs'] - row['avg_runs']) ** 2 +
                (user_stats['bat_high'] - row['high_score']) ** 2 +
                (user_stats['bat_sr'] - row['avg_strike_rate']) ** 2 +
                (user_stats['bat_avg'] - row['avg_bat_avg']) ** 2
            ) ** 0.5
            similarity = 1000 - dist
            results.append({'name': row['player_name'], 'similarity': similarity})
        results.sort(key=lambda x: -x['similarity'])
        print("Top batters:", results[:10])
        return results[:10]

    @classmethod
    def get_top_bowlers(cls, conn, user_stats):
        cur = conn.cursor()
        cur.execute("""
            SELECT p.player_name,
                AVG(bi.overs) AS avg_overs,
                AVG(bi.wickets) AS avg_wkts,
                AVG(bi.runs) AS avg_runs,
                AVG(bi.economy) AS avg_eco
            FROM BBL_Players p
            JOIN BBL_BowlingInnings bi ON p.player_id = bi.player_id
            GROUP BY p.player_id
            HAVING COUNT(*) > 5
        """)
        players = cur.fetchall()
        results = []
        for row in players:
            dist = (
                (user_stats['bowl_overs'] - row['avg_overs']) ** 2 +
                (user_stats['bowl_wkts'] - row['avg_wkts']) ** 2 +
                (user_stats['bowl_runs'] - row['avg_runs']) ** 2 +
                (user_stats['bowl_eco'] - row['avg_eco']) ** 2
            ) ** 0.5
            similarity = 1000 - dist
            results.append({'name': row['player_name'], 'similarity': similarity})
        results.sort(key=lambda x: -x['similarity'])
        return results[:10]