// public/script.js

// Your SportsData API key (used only on teams.html)
const apiKey = 'e1d8945821ee440697559fe48efcd42a';

document.addEventListener('DOMContentLoaded', () => {
  //
  // 1) Teams → Player Cards + Logo logic
  //
  const teamSelect      = document.getElementById('teamSelect');
  const cardContainer   = document.getElementById('playerCards');
  const teamLogo        = document.getElementById('teamLogo');
  const teamLogoSmall   = document.getElementById('teamLogoSmall');
  const teamHeader      = document.getElementById('teamHeader');

  const teamLogos = {
    BOS: 'https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg',
    LAL: 'https://upload.wikimedia.org/wikipedia/commons/3/3c/Los_Angeles_Lakers_logo.svg',
    GS:  'https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg',
    MIA: 'https://upload.wikimedia.org/wikipedia/en/f/fb/Miami_Heat_logo.svg'
    // …add more mapping as needed…
  };

  if (teamSelect && cardContainer) {
    // When team changes:
    teamSelect.addEventListener('change', async () => {
      const key = teamSelect.value;

      // Update logos & header
      if (key && teamLogos[key]) {
        const name = teamSelect.options[teamSelect.selectedIndex].text;
        teamLogo.src        = teamLogos[key];
        teamLogo.alt        = `${name} Logo`;
        teamLogo.style.display      = '';
        teamLogoSmall.src   = teamLogos[key];
        teamLogoSmall.alt   = `${name} Logo`;
        teamLogoSmall.style.display = '';
        teamHeader.textContent = `${name} Roster`;
      } else {
        teamLogo.style.display      = 'none';
        teamLogoSmall.style.display = 'none';
        teamHeader.textContent      = 'Select a Team';
      }

      // Clear old cards
      cardContainer.innerHTML = '';
      if (!key) return;

      // Fetch & render new cards
      await fetchAndRenderCards(key);
    });

    // Auto‐select if URL has ?team=KEY
    const params  = new URLSearchParams(window.location.search);
    const preset  = params.get('team');
    if (preset) {
      teamSelect.value = preset;
      teamSelect.dispatchEvent(new Event('change'));
    }
  }

  async function fetchAndRenderCards(team) {
  // 2) Fetch data
    try {
      const res     = await fetch(
        `https://api.sportsdata.io/v3/nba/scores/json/PlayersBasic/${team}?key=${apiKey}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const players = await res.json();
  
      // 3) Render cards (this will overwrite the spinner)
      
      await renderCards(players);
  
    } catch (err) {
      console.error('Failed to fetch players:', err);
  
      // 4) Show error message instead of spinner
      cardContainer.innerHTML = `
        <div class="col-12 text-center text-danger">
          Error loading players.
        </div>`;
    }
  }

  // Get Wikipedia thumbnail (or placeholder)
  async function getPlayerImage(name) {
    const placeholder = 'https://via.placeholder.com/250x300?text=No+Image';
  
    // 1) Normalize and drop suffixes like "Jr.", "Sr.", "II", "III", "IV"
    let pageName = name.trim().replace(/ +/g, '_');
    pageName = pageName.replace(/_(Jr\.?|Sr\.|I{2,3}|IV)$/i, '');
  
    // 2) Try exact page summary first
    try {
      const exactResp = await fetch(
        `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(pageName)}`
      );
      if (exactResp.ok) {
        const data = await exactResp.json();
        const desc = (data.description||'').toLowerCase();
        if (/basketball|nba/.test(desc)) {
          return data.thumbnail?.source || placeholder;
        }
      }
    } catch {
      /* fall through to fallback */
    }
  
    // 3) Fallback: search for "<name> basketball" (no srwhat=title)
    try {
      const searchUrl =
        'https://en.wikipedia.org/w/api.php' +
        '?action=query' +
        '&list=search' +
        '&srsearch=' + encodeURIComponent(name + ' basketball') +
        '&format=json' +
        '&origin=*';
      const searchResp = await fetch(searchUrl);
      const { query } = await searchResp.json();
      if (query.search && query.search.length) {
        const title = query.search[0].title;
        const sumResp = await fetch(
          `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`
        );
        if (sumResp.ok) {
          const sumData = await sumResp.json();
          const desc = (sumData.description||'').toLowerCase();
          if (/basketball|nba/.test(desc)) {
            return sumData.thumbnail?.source || placeholder;
          }
        }
      }
    } catch {
      /* swallow */
    }
  
    // 4) Ultimate fallback
    return placeholder;
  }
  

  // Render Bootstrap cards in a grid
  async function renderCards(players) {
    const imgUrls = await Promise.all(
      players.map(p => getPlayerImage(`${p.FirstName} ${p.LastName}`))
    );
  
    players.forEach((p, idx) => {
      const imgSrc = imgUrls[idx];
      const col    = document.createElement('div');
      col.className = 'col-sm-6 col-md-4 col-lg-3';
  
      col.innerHTML = `
        <div class="card h-100 shadow-sm">
          <!-- 1) Player photo -->
          <img src="${imgSrc}"
               class="card-img-top"
               alt="${p.FirstName} ${p.LastName}">
  
          <!-- 2) Jersey badge -->
          <span class="badge badge-jersey text-white">#${p.Jersey}</span>
  
          <!-- 3) Body: name & position -->
          <div class="card-body text-center">
            <h5 class="card-title mb-1">
              ${p.FirstName} ${p.LastName}
            </h5>
            <p class="text-muted mb-0">${p.Position}</p>
          </div>
  
          <!-- 4) Quick stats list -->
          <ul class="list-group list-group-flush">
            <li class="list-group-item">
              <span>Born</span>
              <span>${new Date(p.BirthDate).toLocaleDateString()}</span>
            </li>
            <li class="list-group-item">
              <span>Ht</span>
              <span>${p.Height}"</span>
            </li>
            <li class="list-group-item">
              <span>Wt</span>
              <span>${p.Weight} lbs</span>
            </li>
          </ul>
  
          <!-- 5) Footer with full-width button -->
          <div class="card-footer">
            <a href="player.html?id=${p.PlayerID}"
               class="btn btn-primary">
              View Stats
            </a>
          </div>
        </div>`;
  
      cardContainer.appendChild(col);
    });
  }

  //
  // 2) Data.html → Find Your Match form + modal logic
  //
  const form = document.getElementById('userForm');
  if (form) {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const wpct = parseFloat(form.wpct.value);
      const pf   = parseFloat(form.pf.value);
      const pa   = parseFloat(form.pa.value);

      try {
        const res   = await fetch('/nba-stats');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const teams = await res.json();

        let bestTeam = null;
        let minScore = Infinity;
        teams.forEach(team => {
          const pct = team.Percentage * 100;
          const score =
            Math.pow(pct - wpct, 2) +
            Math.pow(team.PointsPerGameFor - pf, 2) +
            Math.pow(team.PointsPerGameAgainst - pa, 2);

          if (score < minScore) {
            minScore = score;
            bestTeam = team;
          }
        });

        if (!bestTeam) {
          alert('No match found. Try different values.');
          return;
        }

        document.getElementById('modalBody').innerHTML = `
          <p>Your closest match is:
            <strong>${bestTeam.City} ${bestTeam.Name}</strong>
            (${bestTeam.Key}).
          </p>`;

        const viewLink = document.getElementById('viewTeamLink');
        viewLink.href   = `teams.html?team=${bestTeam.Key}`;

        new bootstrap.Modal(
          document.getElementById('resultModal')
        ).show();

      } catch (err) {
        console.error('Error finding match:', err);
        alert('Sorry, something went wrong. See console for details.');
      }
    });
  }
});

