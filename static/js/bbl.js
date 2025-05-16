/*  ----------------------------------------------------------------------
    bbl.js - fully refactored for AJAX (no page reload)
    ------------------------------------------------------------------  */

document.addEventListener('DOMContentLoaded', initBBL);

function initBBL() {
  /* helpers */
  const $  = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));
  const csrf = () => document.querySelector('input[name="csrf_token"]')?.value;

  /* ---------- row builders ---------- */
  const buildBatterRows = list => list.map((p,i)=>`
    <tr>
      <td class="rank">${i+1}</td><td>${p.name}</td><td>${p.innings}</td>
      <td>${p.runs}</td><td>${p.high_score}</td>
      <td>${Number(p.bat_avg).toFixed(2)}</td>
      <td>${Number(p.bat_sr ).toFixed(2)}</td>
    </tr>`).join('');

  const buildBowlerRows = list => list.map((p,i)=>`
    <tr>
      <td class="rank">${i+1}</td><td>${p.name}</td><td>${p.overs}</td>
      <td>${p.wickets}</td><td>${p.runs_conceded}</td>
      <td>${Number(p.bowl_avg).toFixed(2)}</td>
      <td>${Number(p.eco     ).toFixed(2)}</td>
    </tr>`).join('');

  const buildSearchRows = list => list.map((p, i) => `
  <tr>
    <td class="rank">${i+1}</td>
    <td>${p.name}</td>
    <td>${p.innings ?? '-'}</td>
    <td>${p.runs ?? '-'}</td>
    <td>${p.high_score ?? '-'}</td>
    <td>${Number(p.bat_avg ?? 0).toFixed(2)}</td>
    <td>${Number(p.bat_sr ?? 0).toFixed(2)}</td>
    <td>${p.wickets ?? '-'}</td>
    <td>${p.bowl_avg != null ? Number(p.bowl_avg).toFixed(2) : '-'}</td>
    <td>${p.eco != null ? Number(p.eco).toFixed(2) : '-'}</td>
  </tr>
`).join('');

  /* ---------- form submit via fetch ---------- */
  const formEl = $('#user-stats-form');
  if (formEl) {
    formEl.addEventListener('submit', ev => {
      ev.preventDefault();
      fetch('/bbl/json', {
        method : 'POST',
        body   : new FormData(formEl),
        headers: { 'X-CSRFToken': csrf() }
      })
      .then(r => r.json())
      .then(updatePage)
      .catch(err => console.error('BBL JSON fetch failed:', err));
    });
  }

  /* -------------------------------------------------------------------
     Update the page with returned JSON
     ----------------------------------------------------------------- */
  /* ---------- response handler ---------- */
  function updatePage({ user, bat, bowl }) {
    window.userStats   = user;
    window.matchesBat  = bat;
    window.matchesBowl = bowl;
    renderResultsTables()
    initRadarCharts?.();            // re-draw charts (defined elsewhere)
    document.querySelector('.radar-container')?.style.setProperty('display', 'block');
    scrollTo('#stats');
  }

  const scrollTo = id => $(id)?.scrollIntoView({behavior:'smooth'});

  /* ---------- (re)build results ---------- */
  function renderResultsTables() {
    /* nuke all previous containers (cleans out the zombie divs) */
    $$('.similar-results-flex').forEach(e => e.remove());

    const box = document.createElement('div');
    box.className = 'similar-results-flex';

    /* batting */
    if (window.matchesBat?.length) {
      box.insertAdjacentHTML('beforeend', `
        <div class="similar-results">
          <h3>Top 10 Similar Batters</h3>
          <table class="similar-table">
            <thead><tr>
              <th class="rank">#</th><th>Name</th><th>Inn</th><th>Runs</th>
              <th>HS</th><th>Avg</th><th>SR</th>
            </tr></thead>
            <tbody>${buildBatterRows(window.matchesBat)}</tbody>
          </table>
        </div>`);
    }

    /* bowling */
    if (window.matchesBowl?.length) {
      box.insertAdjacentHTML('beforeend', `
        <div class="similar-results">
          <h3>Top 10 Similar Bowlers</h3>
          <table class="similar-table">
            <thead><tr>
              <th class="rank">#</th><th>Name</th><th>Ov</th><th>Wkts</th>
              <th>Runs Ccd</th><th>Avg</th><th>Eco</th>
            </tr></thead>
            <tbody>${buildBowlerRows(window.matchesBowl)}</tbody>
          </table>
        </div>`);
    }

    /* place the whole block *after* the form */
    $('#user-stats-form')?.after(box);
  }

  /* ---------- player search / team stats (unchanged) ---------- */
  $('#player-search-btn')?.addEventListener('click', () => {
    const q = $('#player-search-input')?.value.trim();
    if (!q) return;
    fetch(`/bbl/player_search?q=${encodeURIComponent(q)}`)
      .then(r=>r.json()).then(showPlayerSearch);
  });

  const showPlayerSearch = res => {
    $('#player-results').innerHTML = res.length ? `
      <div class="similar-results"><table class="similar-table">
        <thead><tr>
          <th class="rank">#</th><th>Name</th><th>Inn</th><th>Runs</th>
          <th>HS</th><th>Avg</th><th>SR</th><th>Wkts</th><th>BAvg</th><th>Eco</th>
        </tr></thead>
        <tbody>${buildSearchRows(res)}</tbody>
      </table></div>` : '<p>No players found.</p>';
  };

  /* team list / stats stripped for brevity - unchanged */


  /* -------------------------------------------------------------------
     TEAM LIST & TEAM STATS (unchanged)
     ----------------------------------------------------------------- */
  // populate drop-down
  fetch('/bbl/team_list')
    .then(r => r.json())
    .then(list => {
      const sel = document.getElementById('team-select');
      list.forEach(t => sel?.insertAdjacentHTML('beforeend',
        `<option value="${t}">${t}</option>`));
    });

  document.getElementById('team-select')?.addEventListener('change', e => {
    const team = e.target.value;
    if (!team) return $('#team-results').innerHTML = '';
    fetch(`/bbl/team_stats?team=${encodeURIComponent(team)}`)
      .then(r => r.json())
      .then(renderTeamStats);
  });

  function renderTeamStats(d) {
    $('#team-results').innerHTML = d.team ? `
      <table class="team-table">
        <tr><th colspan="2">${d.team}</th></tr>
        <tr><td>Matches</td><td>${d.matches}</td></tr>
        <tr><td>Wins</td><td>${d.wins}</td></tr>
        <tr><td>Losses</td><td>${d.losses}</td></tr>
        <tr><td>Win %</td><td>${d.win_pct}</td></tr>
        <tr><td>Favoured opponent</td>
            <td>${d.best_vs} (${d.best_vs_wins} wins)</td></tr>
        <tr><td>Toughest opponent</td>
            <td>${d.worst_vs} (${d.worst_vs_losses} losses)</td></tr>
        <tr><td>Seasons won</td>
            <td>${d.seasons_won.join(', ') || '-'}</td></tr>
      </table>` : '';
  }

  /* -------------------------------------------------------------------
     RADAR CHARTS  (ECharts 5) - unchanged except for dispose()
     ----------------------------------------------------------------- */
  const CAPS = { batting:{ innings:150,runs:3000,high:200,avg:100,sr:220 },
                 bowling:{ overs:400,wkts:150,runsCon:3000,avg:100,eco:15 } };

  function clamp(v, max){ return Math.min(v ?? 0, max); }
  const firstN = (arr, n=5) => Array.isArray(arr) ? arr.slice(0, n) : [];

  function buildRadar({elId, indicators, userValues, peerValues}) {
    const el = document.getElementById(elId);
    if (!el) return;

    // dispose previous chart if any
    if (window.echarts.getInstanceByDom(el)) {
      window.echarts.getInstanceByDom(el).dispose();
    }
    const chart = window.echarts.init(el);

    chart.setOption({
      tooltip:{},
      legend:{ type:'scroll' },
      radar:{ indicator:indicators, splitNumber:5 },
      series:[{ type:'radar',
                data:[
                  { name:'You', value:userValues,
                    lineStyle:{width:2,color:'#000'},
                    itemStyle:{color:'#000'},
                    symbol:'none', areaStyle:{opacity:0.05} },
                  ...peerValues
                ]}]
    });
  }

  function initRadarCharts(){
    if (!window.userStats) return;

    /* batting */
    if (window.userStats.bat_innings){
      buildRadar({
        elId:'bat-radar',
        indicators:[
          {name:'Innings', max:CAPS.batting.innings},
          {name:'Runs',    max:CAPS.batting.runs},
          {name:'High',    max:CAPS.batting.high},
          {name:'Average', max:CAPS.batting.avg},
          {name:'SR',      max:CAPS.batting.sr}
        ],
        userValues:[
          clamp(window.userStats.bat_innings, CAPS.batting.innings),
          clamp(window.userStats.bat_runs,    CAPS.batting.runs),
          clamp(window.userStats.bat_high,    CAPS.batting.high),
          clamp(window.userStats.bat_avg,     CAPS.batting.avg),
          clamp(window.userStats.bat_sr,      CAPS.batting.sr)
        ],
        peerValues: firstN(window.matchesBat).map(p => ({
          name:p.name,
          value:[
            clamp(p.innings, CAPS.batting.innings),
            clamp(p.runs,    CAPS.batting.runs),
            clamp(p.high_score, CAPS.batting.high),
            clamp(p.bat_avg, CAPS.batting.avg),
            clamp(p.bat_sr,  CAPS.batting.sr)
          ],
          lineStyle:{type:'dashed', width:1}
        }))
      });
    }

    /* bowling */
    if (window.userStats.bowl_overs){
      buildRadar({
        elId:'bowl-radar',
        indicators:[
          {name:'Overs', max:CAPS.bowling.overs},
          {name:'Wkts',  max:CAPS.bowling.wkts},
          {name:'Runs con', max:CAPS.bowling.runsCon},
          {name:'Avg',   max:CAPS.bowling.avg},
          {name:'Eco',   max:CAPS.bowling.eco}
        ],
        userValues:[
          clamp(window.userStats.bowl_overs, CAPS.bowling.overs),
          clamp(window.userStats.bowl_wkts,  CAPS.bowling.wkts),
          clamp(window.userStats.bowl_runs,  CAPS.bowling.runsCon),
          clamp(window.userStats.bowl_avg,   CAPS.bowling.avg),
          clamp(window.userStats.bowl_eco,   CAPS.bowling.eco)
        ],
        peerValues: firstN(window.matchesBowl).map(p => ({
          name:p.name,
          value:[
            clamp(p.overs,  CAPS.bowling.overs),
            clamp(p.wickets, CAPS.bowling.wkts),
            clamp(p.runs,    CAPS.bowling.runsCon),
            clamp(p.bowl_avg,CAPS.bowling.avg),
            clamp(p.eco,     CAPS.bowling.eco)
          ],
          lineStyle:{type:'dashed', width:1}
        }))
      });
    }
  }
}

// Needs html2canvas (already linked right above the fragment)
document.addEventListener('DOMContentLoaded', () => {
  const btn   = document.getElementById('share-btn');
  const users = document.getElementById('share-users');
  const text  = document.getElementById('share-text');
  const csrf  = document.querySelector('meta[name="csrf-token"]').content;

  btn.addEventListener('click', async () => {
    // 1. Work out which radar divs exist & are rendered
    const radarIds = ['bat-radar', 'bowl-radar']
                      .map(id => document.getElementById(id))
                      .filter(el => el && el.childElementCount);

    if (!radarIds.length) {
      alert('No charts to share yet!');
      return;
    }

    // 2. Snapshot each radar
    const canvases = await Promise.all(
      radarIds.map(el => html2canvas(el, {backgroundColor: null}))
    );

    // 3. Stitch vertically into one image
    const combo = document.createElement('canvas');
    combo.width  = Math.max(...canvases.map(c => c.width));
    combo.height = canvases.reduce((h, c) => h + c.height, 0);
    const ctx = combo.getContext('2d');
    let y = 0;
    canvases.forEach(c => { ctx.drawImage(c, 0, y); y += c.height; });
    const imgData = combo.toDataURL('image/png');

    // 4. Build payload
    const payload = {
      league      : 'bbl',
      image       : imgData,
      text        : text.value || 'BBL radar comparison',
      shared_with : (users.value || 'ALL').split(',').map(u => u.trim())
    };

    // 5. POST to the existing endpoint
    try {
      const res = await fetch('/submit_post', {
        method : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken' : csrf
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        // alert('Posted to forum!');
        users.value = ''; text.value = '';
        window.location.href = '/all_posts';
      } else {
        alert('Error posting: ' + res.statusText + ': ' + res.text());
        throw new Error(await res.text());
      }
    } catch (err) {
      alert('Error posting: ' + err.message);
    }
  });
});
