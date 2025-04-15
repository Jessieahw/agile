// server.js

const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();
const port = 3000;  // You can change the port if needed

// Serve static files from the "public" directory
app.use(express.static(path.join(__dirname, 'public')));

// API endpoint to fetch NBA standings
app.get('/nba-stats', async (req, res) => {
  try {
    // Directly use the URL provided (hard-coded API key)
    const apiUrl = 'https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key=e1d8945821ee440697559fe48efcd42a';
    const response = await axios.get(apiUrl);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching data:', error.message);
    res.status(500).json({ error: 'Failed to fetch data from SportsDataIO API' });
  }
});

// Optionally, define a route for the root URL to serve index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

