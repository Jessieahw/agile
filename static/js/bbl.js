document.addEventListener('DOMContentLoaded', () => {
  const $ = sel => document.querySelector(sel);

  // Helper builders
  const buildPlayerRows = (data) => data.map((p,i)=>`<tr><td class=\"rank\">${i+1}</td><td>${p.name}</td><td>${p.innings}</td><td>${p.runs}</td><td>${p.high_score}</td><td>${Number(p.bat_avg).toFixed(2)}</td><td>${Number(p.bat_sr).toFixed(2)}</td><td>${p.wickets??'-'}</td><td>${p.bowl_avg?Number(p.bowl_avg).toFixed(2):'-'}</td><td>${p.eco?Number(p.eco).toFixed(2):'-'}</td></tr>`).join('');
  const buildTeamRows = (data) => data.map((t,i)=>`<tr><td class=\"rank\">${i+1}</td><td>${t.team}</td><td>${t.played}</td><td>${t.wins}</td><td>${t.win_pct}</td></tr>`).join('');

  // Player search
  $('#player-search-btn').addEventListener('click', () => {
    const q = $('#player-search-input').value.trim(); if(!q) return;
    fetch(`/bbl/player_search?q=${encodeURIComponent(q)}`).then(r=>r.json()).then(d=>{
      if(!d.length){ $('#player-results').innerHTML='<p>No players found.</p>'; return; }
      $('#player-results').innerHTML = `<div class=\"similar-results\"><h3>Players</h3><table class=\"similar-table\"><thead><tr><th class=rank>#</th><th>Name</th><th>Inn</th><th>Runs</th><th>HS</th><th>Avg</th><th>SR</th><th>Wkts</th><th>BAvg</th><th>Eco</th></tr></thead><tbody>${buildPlayerRows(d)}</tbody></table></div>`;
    });
  });

  // Team search
  $('#team-search-btn').addEventListener('click', () => {
    const q = $('#team-search-input').value.trim(); if(!q) return;
    fetch(`/bbl/team_search?q=${encodeURIComponent(q)}`).then(r=>r.json()).then(d=>{
      if(!d.length){ $('#team-results').innerHTML='<p>No teams found.</p>'; return; }
      $('#team-results').innerHTML = `<div class=\"similar-results\"><h3>Teams</h3><table class=\"similar-table\"><thead><tr><th class=rank>#</th><th>Team</th><th>Played</th><th>Wins</th><th>Win %</th></tr></thead><tbody>${buildTeamRows(d)}</tbody></table></div>`;
    });
  });
});

// Team Search
function renderTeamStats(dt){
  const wrap = document.getElementById('team‑results');
  wrap.innerHTML = dt.team ? `
    <table class="team‑table">
      <tr><th colspan="2">${dt.team}</th></tr>
      <tr><td>Matches</td><td>${dt.matches}</td></tr>
      <tr><td>Wins</td><td>${dt.wins}</td></tr>
      <tr><td>Losses</td><td>${dt.losses}</td></tr>
      <tr><td>Win&nbsp;%</td><td>${dt.win_pct}</td></tr>
      <tr><td>Favoured opponent</td><td>${dt.best_vs} (${dt.best_vs_wins} wins)</td></tr>
      <tr><td>Toughest opponent</td><td>${dt.worst_vs} (${dt.worst_vs_losses} losses)</td></tr>
      <tr><td>Seasons won</td><td>${dt.seasons_won.join(', ') || '–'}</td></tr>
    </table>` : '';
}
// Team list route getter
fetch('/bbl/team_list').then(r=>r.json()).then(list=>{
  const sel = document.getElementById('team‑select');
  list.forEach(t=>{
    const o = document.createElement('option');
    o.value = o.textContent = t;
    sel.appendChild(o);
  });
});
// Team stats updater on new team selection:
document.getElementById('team‑select').addEventListener('change', e=>{
  const v = e.target.value;
  if(!v){ document.getElementById('team‑results').innerHTML=''; return; }
  fetch(`/bbl/team_stats?team=${encodeURIComponent(v)}`)
    .then(r=>r.json())
    .then(renderTeamStats);
});