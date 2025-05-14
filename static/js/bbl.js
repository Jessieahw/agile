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
      $('#player-results').innerHTML = `<div class=\"similar-results\"><table class=\"similar-table\"><thead><tr><th class=rank>#</th><th>Name</th><th>Inn</th><th>Runs</th><th>HS</th><th>Avg</th><th>SR</th><th>Wkts</th><th>BAvg</th><th>Eco</th></tr></thead><tbody>${buildPlayerRows(d)}</tbody></table></div>`;
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
/* Constants to cap the RADAR sheets */
const CAPS = {
  batting: {
    innings: 150,
    runs:    3000,
    high:    200,
    avg:     100,
    sr:      220
  },
  bowling: {
    overs:   400,
    wkts:    150,
    runsCon: 3000,
    avg:     100,
    eco:     15
  }
};

/* Helper Functions for the RADAR Sheets*/
/** Clamp a value to an upper bound (null/undefined → 0). */
function clamp (v, max) {
  return Math.min(v ?? 0, max);
}

/** Return up to first n items of arr or [] if arr false. */
function firstN (arr, n = 5) {
  return Array.isArray(arr) ? arr.slice(0, n) : [];
}

/** Initialise one radar chart. */
function buildRadar ({ elId, caps, indicators, userValues, peerValues }) {
  const el = document.getElementById(elId);
  if (!el) return; // canvas/div not on page

  const chart = echarts.init(el);

  const seriesData = [
    {
      name: 'You',
      value: userValues,
      lineStyle: { width: 2, color: '#000' },
      itemStyle:  { color:  '#000' }, 
      symbol: 'none',
      areaStyle: { opacity: 0.05 }
    },
    ...peerValues
  ];

  chart.setOption({
    tooltip: {},
    legend: { type: 'scroll' },
    radar: {
      indicator: indicators,
      splitNumber: 5
    },
    series: [
      {
        type: 'radar',
        data: seriesData
      }
    ]
  });
}

/* Actual build method for the charts */
function initRadarCharts () {
  // Exit early if no user stats are available
  if (!window.userStats) return;

  const batPeers  = firstN(window.matchesBat);
  const bowlPeers = firstN(window.matchesBowl);

  /* Build the batting RADAR chart */
  buildRadar({
    elId: 'bat-radar',
    caps: CAPS.batting,
    indicators: [
      { name: 'Innings', max: CAPS.batting.innings },
      { name: 'Runs',    max: CAPS.batting.runs    },
      { name: 'High',    max: CAPS.batting.high    },
      { name: 'Average', max: CAPS.batting.avg     },
      { name: 'SR',      max: CAPS.batting.sr      }
    ],
    userValues: [
      clamp(window.userStats.bat_innings, CAPS.batting.innings),
      clamp(window.userStats.bat_runs,    CAPS.batting.runs),
      clamp(window.userStats.bat_high,    CAPS.batting.high),
      clamp(window.userStats.bat_avg,     CAPS.batting.avg),
      clamp(window.userStats.bat_sr,      CAPS.batting.sr)
    ],
    peerValues: batPeers.map(p => ({
      name: p.name || 'Peer',
      value: [
        clamp(p.innings,    CAPS.batting.innings),
        clamp(p.runs,       CAPS.batting.runs),
        clamp(p.high_score, CAPS.batting.high),
        clamp(p.bat_avg,    CAPS.batting.avg),
        clamp(p.bat_sr,     CAPS.batting.sr)
      ],
      lineStyle: { type: 'dashed', width: 1 }
    }))
  });

  /* Bowling Radar Chart */
  buildRadar({
    elId: 'bowl-radar',
    caps: CAPS.bowling,
    indicators: [
      { name: 'Overs',     max: CAPS.bowling.overs   },
      { name: 'Wkts',      max: CAPS.bowling.wkts    },
      { name: 'Runs conc', max: CAPS.bowling.runsCon },
      { name: 'Avg',       max: CAPS.bowling.avg     },
      { name: 'Eco',       max: CAPS.bowling.eco     }
    ],
    userValues: [
      clamp(window.userStats.bowl_overs, CAPS.bowling.overs),
      clamp(window.userStats.bowl_wkts,  CAPS.bowling.wkts),
      clamp(window.userStats.bowl_runs,  CAPS.bowling.runsCon),
      clamp(window.userStats.bowl_avg,   CAPS.bowling.avg),
      clamp(window.userStats.bowl_eco,   CAPS.bowling.eco)
    ],
    peerValues: bowlPeers.map(p => ({
      name: p.name || 'Peer',
      value: [
        clamp(p.overs,  CAPS.bowling.overs),
        clamp(p.wickets,CAPS.bowling.wkts),
        clamp(p.runs,   CAPS.bowling.runsCon),
        clamp(p.bowl_avg,CAPS.bowling.avg),
        clamp(p.eco,    CAPS.bowling.eco)
      ],
      lineStyle: { type: 'dashed', width: 1 }
    }))
  });
}

/* Add the event to initialise when the content finishes loading */
document.addEventListener('DOMContentLoaded', initRadarCharts);