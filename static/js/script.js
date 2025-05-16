// public/js/script.js

// Your SportsDataIO API key
const apiKey = 'e1d8945821ee440697559fe48efcd42a';

/**
 * Fetch the 2025 NBA standings directly from SportsDataIO
 */
async function fetchStandings() {
  const res = await fetch(
    `https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key=${apiKey}`,
    { headers: { 'Accept': 'application/json' } }
  );
  if (!res.ok) throw new Error(`Standings fetch failed: ${res.status}`);
  return res.json();
}

/**
 * Populate the team-selector <select> with options
 */
function populateTeamSelector(standings) {
  const sel = document.getElementById('team-selector');
  sel.innerHTML = '<option value="" disabled selected>Select a team</option>';
  standings.forEach(team => {
    const opt = document.createElement('option');
    opt.value       = team.Key;
    opt.textContent = `${team.City} ${team.Name} (${team.Key})`;
    sel.appendChild(opt);
  });
}

/**
 * Display the stats table for a specific team Key
 */
async function displayTeamStats(key) {
  const statsContainer = document.getElementById('team-stats-container');
  try {
    const standings = await fetchStandings();
    const team = standings.find(t => t.Key === key);
    if (!team) {
      statsContainer.innerHTML = '<p>No data found for this team.</p>';
      return;
    }
    const logo = `/static/logos/${team.Key}.png`;
    statsContainer.innerHTML = `
      <table class="table table-bordered stats-table"
             style="background: url('${logo}') no-repeat center center;">
        <thead>
          <tr><th>Field</th><th>Value</th></tr>
        </thead>
        <tbody>
          <tr><td>Season</td><td>${team.Season}</td></tr>
          <tr><td>Team</td><td>${team.City} ${team.Name} (${team.Key})</td></tr>
          <tr><td>Conference</td><td>${team.Conference}</td></tr>
          <tr><td>Division</td><td>${team.Division}</td></tr>
          <tr><td>Wins</td><td>${team.Wins}</td></tr>
          <tr><td>Losses</td><td>${team.Losses}</td></tr>
          <tr><td>Win %</td><td>${(team.Percentage * 100).toFixed(1)}%</td></tr>
          <tr><td>PPG For</td><td>${team.PointsPerGameFor}</td></tr>
          <tr><td>PPG Against</td><td>${team.PointsPerGameAgainst}</td></tr>
          <tr><td>Streak</td><td>${team.StreakDescription}</td></tr>
          <tr><td>Games Back</td><td>${team.GamesBack}</td></tr>
        </tbody>
      </table>`;
  } catch (err) {
    console.error('Error displaying stats:', err);
    statsContainer.innerHTML =
      '<p class="text-danger">Error loading team stats.</p>';
  }
}

/**
 * Fetch & render player cards for a given team key
 */
async function fetchAndRenderCards(teamKey) {
  const cardContainer = document.getElementById('playerCards');
  try {
    const res = await fetch(
      `https://api.sportsdata.io/v3/nba/scores/json/PlayersBasic/${teamKey}?key=${apiKey}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const players = await res.json();
    await renderCards(players);
  } catch (err) {
    console.error('Failed to fetch players:', err);
    cardContainer.innerHTML = `
      <div class="col-12 text-center text-danger">
        Error loading players.
      </div>`;
  }
}

/**
 * Get a player's image from Wikipedia (fallback to placeholder)
 */
async function getPlayerImage(name) {
  const placeholder = 'https://via.placeholder.com/250x300?text=No+Image';

  const staticOverrides = {
    'Scotty Pippen Jr.': '/static/nba_logos/scotty.jpg',
    // add more: 'LeBron James': '/static/images/players/lebron_james.png'
  };
  if (staticOverrides[name]) {
    return staticOverrides[name];
  }
  let page = name.trim().replace(/ +/g, '_')
              .replace(/_(Jr\.?|Sr\.|I{2,3}|IV)$/i, '');
  // Try exact summary
  try {
    const resp = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(page)}`
    );
    if (resp.ok) {
      const data = await resp.json();
      if (/basketball|nba/.test((data.description||'').toLowerCase())) {
        return data.thumbnail?.source || placeholder;
      }
    }
  } catch {}
  // Fallback search
  try {
    const searchUrl = 'https://en.wikipedia.org/w/api.php'
      + '?action=query&list=search'
      + `&srsearch=${encodeURIComponent(name + ' basketball')}`
      + '&format=json&origin=*';
    const sresp = await fetch(searchUrl);
    const { query } = await sresp.json();
    if (query.search?.length) {
      const title = query.search[0].title;
      const sumResp = await fetch(
        `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`
      );
      if (sumResp.ok) {
        const sumData = await sumResp.json();
        if (/basketball|nba/.test((sumData.description||'').toLowerCase())) {
          return sumData.thumbnail?.source || placeholder;
        }
      }
    }
  } catch {}
  return placeholder;
}

/**
 * Render player cards into the #playerCards container
 */
async function renderCards(players) {
  const cardContainer = document.getElementById('playerCards');
  const imgUrls = await Promise.all(
    players.map(p => getPlayerImage(`${p.FirstName} ${p.LastName}`))
  );
  cardContainer.innerHTML = ''; // clear old
  players.forEach((p, idx) => {
    const col = document.createElement('div');
    col.className = 'col-sm-6 col-md-4 col-lg-3';
    col.innerHTML = `
      <div class="card h-100 shadow-sm">
        <img src="${imgUrls[idx]}"  style="width:100%;height:350px;object-fit:cover;object-position:50% 15%;" class="card-img-top player-photo" alt="${p.FirstName} ${p.LastName}">
        <span class="badge badge-jersey text-white">#${p.Jersey}</span>
        <div class="card-body text-center py-3">
          <h5 class="card-title mb-1">${p.FirstName} ${p.LastName}</h5>
          <p class="text-muted mb-0">${p.Position}</p>
        </div>
        <hr class="my-0">
        <div class="card-footer bg-white border-0 text-center py-3">
          <button class="btn btn-primary view-stats-btn" data-index="${idx}">
            View Stats
          </button>
        </div>
      </div>`;
    cardContainer.appendChild(col);
  });
  attachStatsHandlers(players);
}

/**
 * Attach click handlers to the "View Stats" buttons in player cards
 */
function attachStatsHandlers(players) {
  document.querySelectorAll('.view-stats-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = players[btn.dataset.index];
      const body = document.getElementById('playerStatsBody');
      body.innerHTML = `
        <dl class="row">
          <dt class="col-sm-4">Status</dt><dd class="col-sm-8">${p.Status}</dd>
          <dt class="col-sm-4">Team</dt><dd class="col-sm-8">${p.Team}</dd>
          <dt class="col-sm-4">Position</dt><dd class="col-sm-8">${p.Position}</dd>
          <dt class="col-sm-4">Height</dt><dd class="col-sm-8">${p.Height}"</dd>
          <dt class="col-sm-4">Weight</dt><dd class="col-sm-8">${p.Weight} lbs</dd>
          <dt class="col-sm-4">Birth Date</dt><dd class="col-sm-8">${new Date(p.BirthDate).toLocaleDateString()}</dd>
          <dt class="col-sm-4">Birth Place</dt><dd class="col-sm-8">${p.BirthCity}, ${p.BirthState}, ${p.BirthCountry}</dd>
        </dl>`;
      new bootstrap.Modal(document.getElementById('playerStatsModal')).show();
    });
  });
}

async function displayTeamLeaders(teamKey) {
  const leadersContainer = document.getElementById('team-leaders-container');
  leadersContainer.innerHTML = ''; // clear old

  try {
    const res = await fetch(`/nba/team_players/${teamKey}`);
    if (!res.ok) throw new Error(`Leader fetch failed: ${res.status}`);
    const leaders = await res.json();

    if (leaders.length === 0) {
      leadersContainer.innerHTML =
        '<p class="text-center text-muted">No player data available for this team.</p>';
      return;
    }

    const rows = leaders.map(p => `
      <tr>
        <td>${p.name}</td>
        <td>${p.pts}</td>
        <td>${p.ast}</td>
        <td>${p.stl}</td>
        <td>${p.blk}</td>
      </tr>
    `).join('');

    leadersContainer.innerHTML = `
      <h5 class="text-center mb-3">Player Preview</h5>
      <table class="table table-borderless stats-table">
        <thead>
          <tr>
            <th>Player</th><th>PTS</th><th>AST</th><th>STL</th><th>BLK</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  } catch (err) {
    console.error('Error loading team leaders:', err);
    leadersContainer.innerHTML =
      '<p class="text-danger text-center">Couldn’t load team leaders.</p>';
  }
}

async function updateTeamStats(teamKey) {
  await displayTeamStandings(teamKey);
  await displayTeamLeaders(teamKey);
}

document.addEventListener('DOMContentLoaded', () => {
  //
  // INDEX PAGE → Populate dropdown & show stats
  //
  const teamSelector   = document.getElementById('team-selector');
  const statsContainer = document.getElementById('team-stats-container');
  if (teamSelector && statsContainer) {
    fetchStandings()
      .then(populateTeamSelector)
      .catch(err => {
        console.error(err);
        statsContainer.innerHTML = '<p class="text-danger">Error loading data.</p>';
      });
    teamSelector.addEventListener('change', e => displayTeamStats(e.target.value));
    teamSelector.addEventListener('change', e => displayTeamLeaders(e.target.value));
  }

  //
  // TEAMS PAGE → Player Cards + Logo logic
  //
  const teamSelect    = document.getElementById('teamSelect');
  const cardContainer = document.getElementById('playerCards');
  const teamLogo      = document.getElementById('teamLogo');
  const teamLogoSmall = document.getElementById('teamLogoSmall');
  const teamHeader    = document.getElementById('teamHeader');
  
  const teamLogos = window.teamLogos || {};


  

  if (teamSelect && cardContainer) {
    teamSelect.addEventListener('change', async () => {
      const key = teamSelect.value;
      // update logos & header
      if (key && teamLogos[key]) {
        const name = teamSelect.options[teamSelect.selectedIndex].text;
        teamLogoSmall.src   = teamLogos[key];
        teamLogoSmall.alt   = `${name} Logo`;
        teamLogoSmall.style.display = '';
        teamHeader.textContent = `${name} Roster`;
      } else {
        teamLogo.style.display      = 'none';
        teamLogoSmall.style.display = 'none';
        teamHeader.textContent      = 'Select a Team';
      }
      // clear old cards
      cardContainer.innerHTML = '';
      if (key) await fetchAndRenderCards(key);
      
      slideToTeam(key);
    });
    
    // auto‐select from URL
    const params = new URLSearchParams(window.location.search);
    const preset = params.get('team');
    if (preset ) {
      teamSelect.value = preset;
      teamSelect.dispatchEvent(new Event('change'));

      slideToTeam(preset);
    }
  }

  //
  // DATA PAGE → Find Your Match form + modal logic
  //
  const form = document.getElementById('userForm');
  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const wpct = parseFloat(form.wpct.value);
      const pf   = parseFloat(form.pf.value);
      const pa   = parseFloat(form.pa.value);
      let teams;
      try {
        teams = await fetchStandings();
      } catch (err) {
        console.error('Error fetching standings:', err);
        alert('Could not load team data.');
        return;
      }
      let best = null, minScore = Infinity;
      teams.forEach(t => {
        const pct   = t.Percentage * 100;
        const score = (pct - wpct)**2
                    + (t.PointsPerGameFor - pf)**2
                    + (t.PointsPerGameAgainst - pa)**2;
        if (score < minScore) {
          minScore = score;
          best     = t;
        }
      });
      if (!best) {
        alert('No match found. Try different values.');
        return;
      }
      document.getElementById('modalBody').innerHTML = `
        <p>Your closest match is:
          <strong>${best.City} ${best.Name}</strong> (${best.Key}).
        </p>`;
      const link = document.getElementById('viewTeamLink');
      link.href = `${window.teamsBase}?team=${best.Key}`;
      document.getElementById('result').value = best.Key;
      new bootstrap.Modal(
        document.getElementById('resultModal')
      ).show();
    });
  }
});


// Grab the carousel element and Bootstrap instance
const carouselEl = document.getElementById('logoCarousel');
const carousel   = bootstrap.Carousel.getOrCreateInstance(carouselEl, {
  interval: 5000,  // or whatever auto‐rotate interval you want
  wrap:     true   // allow wrap once auto‐rotation restarts
});

// Lock state and idle timer handle
let locked    = false;
let idleTimer = null;

/**
 * Prevent manual or auto slides while locked
 */
carouselEl.addEventListener('slide.bs.carousel', e => {
  if (locked) {
    e.preventDefault();
  }
});

/**
 * Jump to the slide for `key`, lock the carousel,
 * and after 5 minutes, resume auto-rotation from that slide.
 *
 * @param {string} key  – the team code, e.g. "LAL"
 */
function slideToTeam(key) {
  if (!carouselEl) return;

  // Find the index of the slide with data-team===key
  const items = Array.from(carouselEl.querySelectorAll('.carousel-item'));
  const idx   = items.findIndex(item => item.dataset.team === key);
  if (idx < 0) return;

  // Temporarily unlock so .to() can run
  const wasLocked = locked;
  locked = false;

  // Jump to desired slide
  carousel.to(idx);

  // Re-lock and pause auto‐rotation
  locked = true;
  carousel.pause();

  // Clear any existing idle timer
  clearTimeout(idleTimer);

  // After 5 minutes (300 000 ms), unlock and restart auto‐rotation
  idleTimer = setTimeout(() => {
    locked = false;
    // ensure we're still on the chosen slide before cycling
    carousel.to(idx);
    carousel.cycle();
  }, 10000);
}
