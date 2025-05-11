class BBLBestMatchFunctions:
    @classmethod
    def get_top_batters(cls, conn, user_stats):
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.player_name,
                COUNT(*)                    AS innings,
                SUM(b.runs)                 AS total_runs,
                MAX(b.runs)                 AS high_score,
                SUM(b.runs)*1.0/COUNT(*)    AS batting_average,
                AVG(b.runs*100.0/NULLIF(b.balls,0)) AS strike_rate
            FROM BBL_Players p
            JOIN BBL_BattingInnings b ON p.player_id = b.player_id
            GROUP BY p.player_id
            HAVING COUNT(*) > 5
        """)
        players = cur.fetchall()

        scored = []
        for row in players:
            # distance across the same five fields the user enters
            dist = (
                (user_stats['bat_innings']   - row['innings'])          ** 2 +
                (user_stats['bat_runs']      - row['total_runs'])       ** 2 +
                (user_stats['bat_high']      - row['high_score'])       ** 2 +
                (user_stats['bat_avg']       - row['batting_average'])  ** 2 +
                (user_stats['bat_sr']        - row['strike_rate'])      ** 2
            ) ** 0.5
            similarity = 1000 - dist

            scored.append({
                'name':            row['player_name'],
                'innings':         row['innings'],
                'runs':            row['total_runs'],
                'high_score':      row['high_score'],
                'bat_avg':         row['batting_average'],
                'bat_sr':          row['strike_rate'],
                'similarity':      similarity
            })

        # sort & return top-10
        scored.sort(key=lambda x: -x['similarity'])
        return scored[:10]



    @classmethod
    def get_top_bowlers(cls, conn, user_stats):
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.player_name,
                SUM(bi.overs)                       AS overs,
                SUM(bi.wickets)                     AS wickets,
                SUM(bi.runs)                        AS runs_conceded,
                SUM(bi.runs)*1.0/NULLIF(SUM(bi.wickets),0) AS bowling_average,
                SUM(bi.runs)*1.0/NULLIF(SUM(bi.overs),0)   AS economy_rate
            FROM BBL_Players p
            JOIN BBL_BowlingInnings bi ON p.player_id = bi.player_id
            GROUP BY p.player_id
            HAVING COUNT(*) > 5
        """)
        players = cur.fetchall()

        scored = []
        for row in players:
            dist = (
                (user_stats['bowl_overs'] - row['overs'])           ** 2 +
                (user_stats['bowl_wkts']  - row['wickets'])         ** 2 +
                (user_stats['bowl_runs']  - row['runs_conceded'])   ** 2 +
                (user_stats['bowl_avg']   - row['bowling_average']) ** 2 +
                (user_stats['bowl_eco']   - row['economy_rate'])    ** 2
            ) ** 0.5
            similarity = 1000 - dist

            scored.append({
                'name':            row['player_name'],
                'overs':           row['overs'],
                'wickets':         row['wickets'],
                'runs_conceded':   row['runs_conceded'],
                'bowl_avg':        row['bowling_average'],
                'eco':             row['economy_rate'],
                'similarity':      similarity
            })

        scored.sort(key=lambda x: -x['similarity'])
        return scored[:10]
