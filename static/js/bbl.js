/*  static/js/bbl.js  —  SPA version (AJAX + CSRF)  */

document.addEventListener('DOMContentLoaded', () => {
  /* -------------------------------------------------------
     Utilities
  ------------------------------------------------------- */
  const $      = sel => document.querySelector(sel);
  const $$     = sel => document.querySelectorAll(sel);
  const csrf   = () => document.querySelector("meta[name='csrf-token']")?.content || "";

  /* -------------------------------------------------------
     Helpers to build HTML rows for tables
  ------------------------------------------------------- */
  const buildPlayerRows = (data) =>
    data.map(
      (p, i) => `
      <tr>
        <td class="rank">${i + 1}</td>
        <td>${p.name}</td>
        <td>${p.innings}</td>
        <td>${p.runs}</td>
        <td>${p.high_score}</td>
        <td>${Number(p.bat_avg ?? 0).toFixed(2)}</td>
        <td>${Number(p.bat_sr  ?? 0).toFixed(2)}</td>
        <td>${p.wickets ?? '-'}</td>
        <td>${p.bowl_avg ? Number(p.bowl_avg).toFixed(2) : '-'}</td>
        <td>${p.eco      ? Number(p.eco).toFixed(2)      : '-'}</td>
      </tr>`
    ).join('');

  const buildTeamRows = (data) =>
    data.map(
      (t, i) => `
      <tr>
        <td class="rank">${i + 1}</td>
        <td>${t.team}</td>
        <td>${t.played}</td>
        <td>${t.wins}</td>
        <td>${t.win_pct}</td>
      </tr>`
    ).join('');

  /* -------------------------------------------------------
     Player search (unchanged)
  ------------------------------------------------------- */
  $('#player-search-btn')?.addEventListener('click', () => {
    const q = $('#player-search-input').value.trim();
    if (!q) return;

    fetch(`/bbl/player_search?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(d => {
        if (!d.length) {
          $('#player-results').innerHTML = '<p>No players found.</p>';
          return;
        }
        $('#player-results').innerHTML = `
          <div class="similar-results">
            <table class="similar-table">
              <thead>
                <tr>
                  <th class="rank">#</th><th>Name</th><th>Inn</th><th>Runs</th><th>HS</th>
                  <th>Avg</th><th>SR</th><th>Wkts</th><th>BAvg</th><th>Eco</th>
                </tr>
              </thead>
              <tbody>${buildPlayerRows(d)}</tbody>
            </table>
          </div>`;
      });
  });

  /* -------------------------------------------------------
     Team list + stats (unchanged)
  ------------------------------------------------------- */
  fetch('/bbl/team_list')
    .then(r => r.json())
    .then(list => {
      const sel = $('#team-select');
      list.forEach(t => {
        const o = document.createElement('option');
        o.value = o.textContent = t;
        sel.appendChild(o);
      });
    });

  $('#team-select')?.addEventListener('change', e => {
    const v = e.target.value;
    if (!v) {
      $('#team-results').innerHTML = '';
      return;
    }
    fetch(`/bbl/team_stats?team=${encodeURIComponent(v)}`)
      .then(r => r.json())
      .then(renderTeamStats);
  });

  /* -------------------------------------------------------
     NEW: AJAX submit for similarity comparison
  ------------------------------------------------------- */
  $('#submit-stats')?.addEventListener('click', async () => {
    const form     = $('#user-stats-form');
    const payload  = Object.fromEntries(new FormData(form).entries());

    try {
      const response = await fetch('/bbl/compare', {
        method : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken' : csrf()          // remove if @csrf_exempt on server
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error(`Status ${response.status}`);
      const { bat, bowl } = await response.json();

      // Update globals so radar charts can reuse them
      window.userStats   = payload;
      window.matchesBat  = bat;
      window.matchesBowl = bowl;

      renderBatTable(bat);
      renderBowlTable(bowl);
      initRadarCharts();                 // rebuild the charts with new data
    } catch (err) {
      console.error('BBL compare failed:', err);
      alert('Sorry — comparison failed. Please try again.');
    }
  });

  /* -------------------------------------------------------
     Render helpers for comparison tables
  ------------------------------------------------------- */
  function ensureResultsFlex () {
    let flex = document.querySelector('.similar-results-flex');
    if (!flex) {
      flex = document.createElement('div');
      flex.className = 'similar-results-flex';
      $('#home').appendChild(flex);
    }
    return flex;
  }

  function renderBatTable (players) {
    if (!players.length) return;
    const flex = ensureResultsFlex();
    flex.querySelector('.bat-results')?.remove(); // clear previous
    const html = `
      <div class="similar-results bat-results">
        <h3>Top 10 Similar Batters</h3>
        <table class="similar-table">
          <thead>
            <tr>
              <th class="rank">#</th><th>Name</th><th>Innings Played</th><th>Total Runs</th>
              <th>Highest Score</th><th>Batting Average</th><th>Strike Rate</th>
            </tr>
          </thead>
          <tbody>${buildPlayerRows(players)}</tbody>
        </table>
      </div>`;
    flex.insertAdjacentHTML('beforeend', html);
  }

  function renderBowlTable (players) {
    if (!players.length) return;
    const flex = ensureResultsFlex();
    flex.querySelector('.bowl-results')?.remove(); // clear previous
    const html = `
      <div class="similar-results bowl-results">
        <h3>Top 10 Similar Bowlers</h3>
        <table class="similar-table">
          <thead>
            <tr>
              <th class="rank">#</th><th>Name</th><th>Overs Bowled</th><th>Wickets</th>
              <th>Runs Conceded</th><th>Bowling Average</th><th>Economy Rate</th>
            </tr>
          </thead>
          <tbody>
            ${players.map((p, i) => `
              <tr>
                <td class="rank">${i + 1}</td>
                <td>${p.name}</td>
                <td>${p.overs}</td>
                <td>${p.wickets}</td>
                <td>${p.runs_conceded}</td>
                <td>${Number(p.bowl_avg ?? 0).toFixed(2)}</td>
                <td>${Number(p.eco      ?? 0).toFixed(2)}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
    flex.insertAdjacentHTML('beforeend', html);
  }

  /* -------------------------------------------------------
     Radar-chart constants + helpers (mostly unchanged)
  ------------------------------------------------------- */
  const CAPS = {
    batting: { innings: 150, runs: 3000, high: 200, avg: 100, sr: 220 },
    bowling: { overs: 400, wkts: 150, runsCon: 3000, avg: 100, eco: 15 }
  };
  const clamp   = (v, m) => Math.min(v ?? 0, m);
  const firstN  = (arr, n = 5) => Array.isArray(arr) ? arr.slice(0, n) : [];

  function buildRadar ({ elId, indicators, userValues, peerValues }) {
    const el = document.getElementById(elId);
    if (!el) return;

    const chart = echarts.init(el);
    chart.setOption({
      tooltip : {},
      legend  : { type: 'scroll' },
      radar   : { indicator: indicators, splitNumber: 5 },
      series  : [{
        type : 'radar',
        data : [
          {
            name      : 'You',
            value     : userValues,
            lineStyle : { width: 2, color: '#000' },
            itemStyle : { color: '#000' },
            symbol    : 'none',
            areaStyle : { opacity: 0.05 }
          },
          ...peerValues
        ]
      }]
    });
  }

  function initRadarCharts () {
    if (!window.userStats) return;

    const batPeers  = firstN(window.matchesBat);
    const bowlPeers = firstN(window.matchesBowl);

    buildRadar({
      elId       : 'bat-radar',
      indicators : [
        { name: 'Innings', max: CAPS.batting.innings },
        { name: 'Runs',    max: CAPS.batting.runs    },
        { name: 'High',    max: CAPS.batting.high    },
        { name: 'Average', max: CAPS.batting.avg     },
        { name: 'SR',      max: CAPS.batting.sr      }
      ],
      userValues : [
        clamp(window.userStats.bat_innings, CAPS.batting.innings),
        clamp(window.userStats.bat_runs,    CAPS.batting.runs),
        clamp(window.userStats.bat_high,    CAPS.batting.high),
        clamp(window.userStats.bat_avg,     CAPS.batting.avg),
        clamp(window.userStats.bat_sr,      CAPS.batting.sr)
      ],
      peerValues : batPeers.map(p => ({
        name      : p.name || 'Peer',
        value     : [
          clamp(p.innings,    CAPS.batting.innings),
          clamp(p.runs,       CAPS.batting.runs),
          clamp(p.high_score, CAPS.batting.high),
          clamp(p.bat_avg,    CAPS.batting.avg),
          clamp(p.bat_sr,     CAPS.batting.sr)
        ],
        lineStyle : { type: 'dashed', width: 1 }
      }))
    });

    buildRadar({
      elId       : 'bowl-radar',
      indicators : [
        { name: 'Overs',     max: CAPS.bowling.overs   },
        { name: 'Wkts',      max: CAPS.bowling.wkts    },
        { name: 'Runs conc', max: CAPS.bowling.runsCon },
        { name: 'Avg',       max: CAPS.bowling.avg     },
        { name: 'Eco',       max: CAPS.bowling.eco     }
      ],
      userValues : [
        clamp(window.userStats.bowl_overs, CAPS.bowling.overs),
        clamp(window.userStats.bowl_wkts,  CAPS.bowling.wkts),
        clamp(window.userStats.bowl_runs,  CAPS.bowling.runsCon),
        clamp(window.userStats.bowl_avg,   CAPS.bowling.avg),
        clamp(window.userStats.bowl_eco,   CAPS.bowling.eco)
      ],
      peerValues : bowlPeers.map(p => ({
        name      : p.name || 'Peer',
        value     : [
          clamp(p.overs,      CAPS.bowling.overs),
          clamp(p.wickets,    CAPS.bowling.wkts),
          clamp(p.runs,       CAPS.bowling.runsCon),
          clamp(p.bowl_avg,   CAPS.bowling.avg),
          clamp(p.eco,        CAPS.bowling.eco)
        ],
        lineStyle : { type: 'dashed', width: 1 }
      }))
    });
  }

  /* Build initial charts if the template embedded data */
  initRadarCharts();
});

/* -------------------------------------------------------
   Team-stats renderer (used above)
------------------------------------------------------- */
function renderTeamStats (dt) {
  const wrap = document.getElementById('team-results');
  wrap.innerHTML = dt.team
    ? `
      <table class="team-table">
        <tr><th colspan="2">${dt.team}</th></tr>
        <tr><td>Matches</td><td>${dt.matches}</td></tr>
        <tr><td>Wins</td><td>${dt.wins}</td></tr>
        <tr><td>Losses</td><td>${dt.losses}</td></tr>
        <tr><td>Win %</td><td>${dt.win_pct}</td></tr>
        <tr><td>Favoured opponent</td><td>${dt.best_vs} (${dt.best_vs_wins} wins)</td></tr>
        <tr><td>Toughest opponent</td><td>${dt.worst_vs} (${dt.worst_vs_losses} losses)</td></tr>
        <tr><td>Seasons won</td><td>${dt.seasons_won.join(', ') || '–'}</td></tr>
      </table>` : '';
}
