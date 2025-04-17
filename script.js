// Your SportsData API key
const apiKey = 'e1d8945821ee440697559fe48efcd42a';

document.addEventListener('DOMContentLoaded', () => {
  const teamSelect = document.getElementById('teamSelect');
  const tbody = document.querySelector('#playersTable tbody');

  // Listen for the user picking a team
  teamSelect.addEventListener('change', async (e) => {
    const team = e.target.value;
    if (!team) {
      tbody.innerHTML = '';          // clear table if no team
      return;
    }
    await fetchAndRender(team);
  });

  // Fetches from the API and then renders the table
  async function fetchAndRender(team) {
    const url = `https://api.sportsdata.io/v3/nba/scores/json/PlayersBasic/${team}?key=${apiKey}`;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const players = await res.json();
      renderPlayers(players);
    } catch (err) {
      console.error('Failed to fetch players:', err);
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">
        Error loading data.
      </td></tr>`;
    }
  }

  // Renders a list of player objects into the <tbody>
  function renderPlayers(players) {
    tbody.innerHTML = '';  // clear old rows

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
  }
});
