// script.js

// 1) Your SportsData API key
const apiKey = 'e1d8945821ee440697559fe48efcd42a';
let ppgChart;
// 2) Map team abbreviations → logo URLs
const teamLogos = {
  BOS: 'https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg',
  LAL: 'https://upload.wikimedia.org/wikipedia/commons/3/3c/Los_Angeles_Lakers_logo.svg',
  GS:  'https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg',
  MIA: 'https://upload.wikimedia.org/wikipedia/en/f/fb/Miami_Heat_logo.svg'
  // …add more as you expand your <select>…
};

document.addEventListener('DOMContentLoaded', () => {
  const teamSelect   = document.getElementById('teamSelect');
  const tbody        = document.querySelector('#playersTable tbody');
  const teamLogoImg  = document.getElementById('teamLogo');
  const teamHeader   = document.getElementById('teamHeader');

  teamSelect.addEventListener('change', async () => {
    const abbr = teamSelect.value;
    tbody.innerHTML = '';              // clear old rows

    // If no selection, reset header + hide logo
    if (!abbr) {
      teamHeader.textContent = 'Select a Team';
      teamLogoImg.style.display = 'none';
      return;
    }

    // 1) Update header text to full team name
    const fullName = teamSelect.options[teamSelect.selectedIndex].text;
    teamHeader.textContent = fullName;

    // 2) Swap in the logo if we have one
    const logoUrl = teamLogos[abbr];
    if (logoUrl) {
      teamLogoImg.src        = logoUrl;
      teamLogoImg.alt        = `${fullName} logo`;
      teamLogoImg.style.display = 'inline-block';
    } else {
      teamLogoImg.style.display = 'none';
    }

    // 3) Fetch & render players
    try {
      const res = await fetch(
        `https://api.sportsdata.io/v3/nba/scores/json/PlayersBasic/${abbr}?key=${apiKey}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const players = await res.json();

      players.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${p.Jersey}</td>
          <td>${p.FirstName} ${p.LastName}</td>
          <td>${p.Position}</td>
          <td>${new Date(p.BirthDate).toLocaleDateString()}</td>
          <td>${p.Height}</td>
          <td>${p.Weight}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error('Error loading players:', err);
      tbody.innerHTML = `
        <tr><td colspan="6" class="text-center text-danger">
          Error loading data.
        </td></tr>
      `;
    }
  });
});


// Handle “Compare” form submission
document.getElementById('userForm').addEventListener('submit', async e => {
  e.preventDefault();
  const f = e.target;
  const payload = {
    wpct: parseFloat(f.wpct.value) / 100,
    pf:   parseFloat(f.pf.value),
    pa:   parseFloat(f.pa.value)
  };

  const resDiv = document.getElementById('results');
  resDiv.innerHTML = `
    <div class="text-center my-4">
      <div class="spinner-border text-primary" role="status"></div>
    </div>`;

  try {
    const r = await fetch('/compare', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const { team, error } = await r.json();

    if (team) {
      resDiv.innerHTML = `
        <div class="alert alert-success">
          Your team is <strong>${team}</strong>
        </div>`;
      // **NEW**: after a successful compare, draw the PPG chart
      drawPPGChart(team).catch(console.error);
    } else {
      resDiv.innerHTML = `
        <div class="alert alert-warning">
          ${error||'No match found'}
        </div>`;
    }
  } catch (err) {
    console.error(err);
    resDiv.innerHTML = `
      <div class="alert alert-danger">
        Error fetching results
      </div>`;
  }
});