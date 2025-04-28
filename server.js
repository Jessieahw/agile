const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();
const port = 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/nba-stats', async (req, res) => {
  try {
    const apiUrl = 'https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key=e1d8945821ee440697559fe48efcd42a';
    const { data } = await axios.get(apiUrl);
    res.json(data);
  } catch (err) {
    console.error('Error fetching NBA stats:', err.message);
    res.status(500).json({ error: 'Failed to fetch NBA standings' });
  }
});

app.post('/compare', async (req, res) => {
  const { wpct: userWpct, pf: userPf, pa: userPa } = req.body;
  try {
    const { data: teams } = await axios.get('https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key=e1d8945821ee440697559fe48efcd42a');

    const scored = teams
      .filter(team => team.PointsPerGameFor != null && team.PointsPerGameAgainst != null && team.Percentage != null)
      .map(team => {
        const stats = {
          wpct: parseFloat(team.Percentage),
          pf: parseFloat(team.PointsPerGameFor),
          pa: parseFloat(team.PointsPerGameAgainst)
        };
        const d1 = stats.wpct - userWpct;
        const d2 = stats.pf - userPf;
        const d3 = stats.pa - userPa;
        const distance = Math.sqrt(d1 * d1 + d2 * d2 + d3 * d3);
        return { team: team.Name, distance };
      });

    const best = scored.sort((a, b) => a.distance - b.distance)[0];

    if (best) {
      res.json({ team: best.team });
    } else {
      res.json({ error: 'No matching team found' });
    }
  } catch (err) {
    console.error('Comparison error:', err.message);
    res.status(500).json({ error: 'Comparison failed' });
  }
});

app.listen(port, () => console.log(`Server listening on http://localhost:${port}`));

