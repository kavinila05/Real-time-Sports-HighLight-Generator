/* ══════════════════════════════════════════
   Dashboard Page — JS
   Loads report, renders all sections,
   handles copilot Q&A and video modal.
══════════════════════════════════════════ */

let REPORT = null;
let VIDEO_ID = null;

/* ────────────────────────────────────────
   Boot
──────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', async () => {
  VIDEO_ID = sessionStorage.getItem('video_id');
  if (!VIDEO_ID) {
    // Try URL param ?id=...
    const params = new URLSearchParams(window.location.search);
    VIDEO_ID = params.get('id');
  }

  if (!VIDEO_ID) {
    // Try to load the latest available report
    try {
      const res  = await fetch('/report/latest');
      if (res.ok) {
        REPORT = await res.json();
        VIDEO_ID = REPORT.video_id || 'latest';
        renderAll();
        return;
      }
    } catch (_) {}

    showGlobalError('No analysis found. Please upload a video first.');
    return;
  }

  await loadReport();
});

async function loadReport() {
  try {
    let url = `/report/${VIDEO_ID}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Report not found');
    REPORT = await res.json();

    if (!REPORT || Object.keys(REPORT).length === 0) {
      showGlobalError('Analysis result is empty. Please try again.');
      return;
    }

    renderAll();
  } catch (err) {
    showGlobalError('Could not load report: ' + err.message);
  }
}

function renderAll() {
  renderStatsGrid();
  renderSummaryBar();
  renderTimeline();
  renderTopMoments();
  renderGallery();
  renderThumbnailStrip();
  renderSpikesChart();
}

/* ────────────────────────────────────────
   STATS GRID
──────────────────────────────────────── */
function renderStatsGrid() {
  const meta     = REPORT.metadata || {};
  const summary  = REPORT.match_summary || {};
  const sport    = cleanSportName(REPORT.sport || 'Unknown');
  const duration = fmtDuration(meta.duration_seconds || 0);
  const fps      = meta.fps || 'N/A';
  const res      = meta.resolution || 'N/A';
  const frames   = meta.frame_count || 'N/A';

  const events        = REPORT.events || [];
  const highlights    = events.filter(e => e.highlight).length;
  const eventBreakdown= summary.event_breakdown || {};

  // Primary stats row
  const statsGrid = document.getElementById('statsGrid');
  statsGrid.innerHTML = '';

  const primary = [
    { label: 'SPORT',        value: sport,           sub: 'Auto detected',            cls: 'sport-name' },
    { label: 'DURATION',     value: duration,        sub: `${frames} frames analyzed`                  },
    { label: 'HIGHLIGHTS',   value: highlights,      sub: 'Key events detected',      cls: 'highlight-tile' },
    { label: 'TOTAL EVENTS', value: events.length,   sub: 'events'                                    },
    { label: 'FPS',          value: fps,             sub: 'video quality'                              },
    { label: 'RESOLUTION',   value: res,             sub: ''                                           },
  ];

  primary.forEach(s => {
    const tile = document.createElement('div');
    tile.className = 'stat-tile' + (s.cls === 'highlight-tile' ? ' highlight-tile' : '');
    tile.innerHTML = `
      <div class="stat-label">${s.label}</div>
      <div class="stat-value ${s.cls === 'sport-name' ? 'sport-name' : ''}">${s.value}</div>
      ${s.sub ? `<div class="stat-sub">${s.sub}</div>` : ''}
    `;
    statsGrid.appendChild(tile);
  });

  // Event breakdown row
  const breakdownGrid = document.getElementById('breakdownGrid');
  breakdownGrid.innerHTML = '';
  Object.entries(eventBreakdown).forEach(([label, count]) => {
    const tile = document.createElement('div');
    tile.className = 'stat-tile';
    tile.innerHTML = `
      <div class="stat-label">${label.replace(/_/g,' ').toUpperCase()}</div>
      <div class="stat-value">${count}</div>
      <div class="stat-sub">events</div>
    `;
    breakdownGrid.appendChild(tile);
  });
}

/* ────────────────────────────────────────
   SUMMARY BAR
──────────────────────────────────────── */
function renderSummaryBar() {
  const sb = document.getElementById('summaryBar');
  const summary = REPORT.match_summary || {};

  let text = '';
  if (typeof summary === 'string') {
    text = summary;
  } else {
    text = summary.body || summary.headline || '';
  }

  if (!text) text = `${cleanSportName(REPORT.sport || '')} analyzed with ${REPORT.event_count || 0} detected events.`;
  sb.innerHTML = '📋 ' + escHtml(text);
}

/* ────────────────────────────────────────
   EVENT TIMELINE
──────────────────────────────────────── */
function renderTimeline() {
  const tl     = document.getElementById('timeline');
  const events = REPORT.events || [];

  if (!events.length) {
    tl.innerHTML = '<div class="empty-state">No events detected.</div>';
    return;
  }

  // Sort by timestamp
  const sorted = [...events].sort((a, b) => a.timestamp - b.timestamp);

  tl.innerHTML = sorted.map(ev => {
    const time       = fmtTime(ev.timestamp);
    const name       = ev.event || 'event';
    const isHL       = ev.highlight;
    const badgeClass = getBadgeClass(name, isHL);
    const badgeText  = getBadgeText(name, isHL);
    const conf       = Math.round((ev.confidence || 0) * 100);
    const audio      = ev.audio_match ? '🔊 crowd cheer' : '';
    const desc       = buildEventDesc(name, time, isHL);

    return `
    <div class="timeline-row">
      <div class="tl-time">${time}</div>
      <div class="tl-content">
        <div><span class="tl-badge ${badgeClass}">${badgeText}</span></div>
        <div class="tl-desc">${escHtml(desc)}</div>
        ${audio ? `<div class="tl-audio-tag">🔊 ${audio}</div>` : ''}
      </div>
    </div>`;
  }).join('');
}

function getBadgeClass(name, isHL) {
  const n = name.toLowerCase();
  if (n.includes('wicket'))                    return 'badge-wicket';
  if (n.includes('six') || n.includes('maximum')) return 'badge-six';
  if (n.includes('boundary'))                  return 'badge-six';
  if (n.includes('goal'))                      return 'badge-goal';
  if (n.includes('slam') || n.includes('dunk')) return 'badge-dunk';
  if (n.includes('3 pointer') || n.includes('three')) return 'badge-dunk';
  if (n.includes('smash'))                     return 'badge-smash';
  if (n.includes('celebrat') || n.includes('scoring')) return 'badge-highlight';
  if (n.includes('penalty') || n.includes('save'))     return 'badge-highlight';
  if (isHL)                                    return 'badge-highlight';
  return 'badge-minor';
}

function getBadgeText(name, isHL) {
  const n = name.toLowerCase();
  if (n.includes('wicket'))                         return 'WICKET!';
  if (n.includes('six') || n.includes('maximum'))   return 'SIX!';
  if (n.includes('boundary'))                       return 'BOUNDARY!';
  if (n.includes('goal'))                           return 'GOAL!';
  if (n.includes('slam') || n.includes('dunk'))     return 'DUNK!';
  if (n.includes('3 pointer') || n.includes('three pointer')) return '3-POINTER!';
  if (n.includes('smash'))                          return 'SMASH!';
  if (n.includes('celebrat'))                       return 'Crowd Celebration';
  if (n.includes('penalty'))                        return 'Penalty';
  if (n.includes('save'))                           return 'Goalkeeper Save';
  if (n.includes('scoring'))                        return 'Score!';
  if (n.includes('rally'))                          return 'Rally';
  if (n.includes('free throw'))                     return 'Free Throw';
  if (n.includes('match point'))                    return 'Match Point!';
  // minor_play / sport-aware non-highlight labels
  if (n.includes('minor_play') || n === 'minor play' ||
      n === 'possession' || n === 'open_play' || n === 'rally') {
    const sport = (REPORT?.sport || '').toLowerCase();
    if (n === 'possession' || sport.includes('basketball')) return 'Possession';
    if (n === 'open_play'  || sport.includes('football'))   return 'Play';
    if (n === 'rally'      || sport.includes('badminton'))  return 'Rally';
    return 'Delivery';
  }
  if (isHL) return 'Highlight';
  return name.replace(/_/g,' ').replace(/\ba\b/g,'').trim().substring(0, 24);
}

function buildEventDesc(name, time, isHL) {
  const n = name.toLowerCase();
  const sport = (REPORT?.sport || '').toLowerCase();
  if (n.includes('wicket'))   return `WICKET at ${time}! Batsman is out! Fans cheering loudly!`;
  if (n.includes('six') || n.includes('maximum')) return `MASSIVE SIX at ${time}! Ball flies out of the ground.`;
  if (n.includes('boundary')) return `BOUNDARY at ${time}! Batsman finds the ropes.`;
  if (n.includes('goal'))     return `GOAL at ${time}! Fans erupting!`;
  if (n.includes('slam') || n.includes('dunk')) return `Slam dunk at ${time}! Crowd going wild!`;
  if (n.includes('3 pointer') || n.includes('three pointer')) return `Three-pointer at ${time}!`;
  if (n.includes('free throw')) return `Free throw attempt at ${time}.`;
  if (n.includes('scoring'))   return `Basket scored at ${time}!`;
  if (n.includes('smash'))     return `Winning smash at ${time}!`;
  if (n.includes('match point')) return `Match point at ${time}!`;
  if (n.includes('rally'))     return `Rally in progress at ${time}.`;
  if (n.includes('celebrat'))  return `Strong crowd reaction at ${time}. Fans cheering loudly!`;
  if (n.includes('penalty'))   return `Penalty awarded at ${time}.`;
  if (n.includes('save'))      return `Goalkeeper save at ${time}!`;
  if (n.includes('minor_play') || n === 'minor play' ||
      n === 'possession' || n === 'open_play' || n === 'rally') {
    if (n === 'possession' || sport.includes('basketball')) return `Possession at ${time}.`;
    if (n === 'open_play'  || sport.includes('football'))   return `Play continues at ${time}.`;
    if (n === 'rally'      || sport.includes('badminton'))  return `Rally at ${time}.`;
    return `Bowler delivers at ${time}.`;
  }
  return `${name.replace(/_/g,' ')} at ${time}.`;
}

/* ────────────────────────────────────────
   TOP MOMENTS
──────────────────────────────────────── */
function renderTopMoments() {
  const ml     = document.getElementById('momentsList');
  const events = REPORT.events || [];

  const top = [...events]
    .filter(e => e.highlight)
    .sort((a, b) => (b.score || b.confidence) - (a.score || a.confidence))
    .slice(0, 5);

  if (!top.length) {
    ml.innerHTML = '<div class="empty-state">No highlight moments found.</div>';
    return;
  }

  const rankColors = ['gold','silver','bronze','',''];
  ml.innerHTML = top.map((ev, i) => {
    const time  = fmtTime(ev.timestamp);
    const name  = formatEventName(ev.event);
    const conf  = Math.round((ev.confidence || 0) * 100);
    const desc  = buildEventDesc(ev.event, time, true);

    return `
    <div class="moment-card" onclick="openMomentModal(${i})">
      <div class="moment-rank ${rankColors[i]}">${i+1}</div>
      <div class="moment-info">
        <div class="moment-name">${escHtml(name)}</div>
        <div class="moment-desc">${escHtml(desc)}</div>
      </div>
      <div class="moment-time">${time}</div>
    </div>`;
  }).join('');

  // Store for modal
  window._topMoments = top;
}

function openMomentModal(idx) {
  const moments = window._topMoments || [];
  const ev = moments[idx];
  if (!ev) return;

  // Try to find a clip for this event from highlight_clips
  const clips = REPORT.highlight_clips || [];
  const match = clips.find(c => Math.abs((c.timestamp||0) - ev.timestamp) < 5);

  if (match && match.clip) {
    openVideoModal(match.clip, match.caption || formatEventName(ev.event), ev);
  }
}

/* ────────────────────────────────────────
   HIGHLIGHT GALLERY
──────────────────────────────────────── */
function renderGallery() {
  const grid  = document.getElementById('galleryGrid');
  const clips = REPORT.highlight_clips || [];

  if (!clips.length) {
    grid.innerHTML = '<div class="empty-state">No highlight clips were generated.</div>';
    return;
  }

  grid.innerHTML = clips.map((c, i) => {
    const rank      = c.rank || (i + 1);
    const name      = formatEventName(c.event);
    const time      = fmtTime(c.timestamp);
    const conf      = Math.round((c.confidence || 0) * 100);
    const confPct   = conf + '%';
    const caption   = c.caption || name;
    const thumbSrc  = c.thumbnail ? `/thumbnails/${getBasename(c.thumbnail)}` : null;
    const clipSrc   = c.clip ? `/highlights/${getBasename(c.clip)}` : null;

    const thumbHtml = thumbSrc
      ? `<img class="gallery-thumb" src="${thumbSrc}" alt="${escHtml(name)}" onerror="this.parentElement.innerHTML='<div class=gallery-thumb-placeholder>🎬</div>'">`
      : `<div class="gallery-thumb-placeholder">🎬</div>`;

    return `
    <div class="gallery-tile" onclick='${clipSrc ? `openVideoModal("${clipSrc}","${escHtml(caption)}",${JSON.stringify({timestamp:c.timestamp,confidence:c.confidence,event:c.event})})` : ''}'>
      <div class="gallery-thumb-wrap">
        ${thumbHtml}
        ${clipSrc ? '<div class="play-overlay">▶</div>' : ''}
      </div>
      <div class="gallery-info">
        <div class="gallery-rank">#${rank} ${c.importance === 'top_highlight' ? '⭐ TOP' : ''}</div>
        <div class="gallery-event">${escHtml(name)}</div>
        <div class="gallery-meta">
          <span>🕐 ${time}</span>
          <span>${confPct}</span>
        </div>
        <div class="conf-bar-wrap">
          <div class="conf-bar-fill" style="width:${confPct}"></div>
        </div>
      </div>
    </div>`;
  }).join('');
}

/* ────────────────────────────────────────
   THUMBNAIL STRIP
   Pure image viewer — one static JPEG per
   highlight, no play button, no video modal.
   Clicking opens a full-size image lightbox.
──────────────────────────────────────── */
function renderThumbnailStrip() {
  const container = document.getElementById('thumbnailStrip');
  if (!container) return;

  const clips = REPORT.highlight_clips || [];

  if (!clips.length) {
    container.innerHTML = '<div class="empty-state">No thumbnails were generated.</div>';
    return;
  }

  container.innerHTML = clips.map((c, i) => {
    const rank     = c.rank || (i + 1);
    const name     = formatEventName(c.event);
    const time     = fmtTime(c.timestamp);
    const conf     = Math.round((c.confidence || 0) * 100);
    const thumbSrc = c.thumbnail ? `/thumbnails/${getBasename(c.thumbnail)}` : null;
    const isTop    = c.importance === 'top_highlight';

    if (!thumbSrc) return '';   // skip if no image was generated

    return `
    <div class="thumb-card ${isTop ? 'thumb-card-top' : ''}"
         onclick="openImageLightbox('${thumbSrc}','${escHtml(name)}','${time}','${conf}')">
      <div class="thumb-card-img-wrap">
        <img class="thumb-card-img"
             src="${thumbSrc}"
             alt="${escHtml(name)}"
             onerror="this.closest('.thumb-card').style.display='none'">
        <div class="thumb-card-zoom">🔍</div>
        ${isTop ? '<div class="thumb-card-top-badge">⭐ TOP</div>' : ''}
        <div class="thumb-card-rank">#${rank}</div>
      </div>
      <div class="thumb-card-meta">
        <div class="thumb-card-name">${escHtml(name)}</div>
        <div class="thumb-card-time">🕐 ${time}</div>
        <div class="thumb-conf-row">
          <div class="thumb-conf-bar">
            <div class="thumb-conf-fill" style="width:${conf}%"></div>
          </div>
          <span class="thumb-conf-label">${conf}%</span>
        </div>
      </div>
    </div>`;
  }).join('');
}

/* ── Image Lightbox ── */
function openImageLightbox(src, name, time, conf) {
  // Reuse the video modal structure for the image lightbox
  const modal = document.getElementById('videoModal');
  const meta  = document.getElementById('modalMeta');
  const video = document.getElementById('modalVideo');

  // Hide the video element, show an image instead
  video.style.display = 'none';

  // Remove any existing lightbox image
  const existing = document.getElementById('lightboxImg');
  if (existing) existing.remove();

  const img = document.createElement('img');
  img.id = 'lightboxImg';
  img.src = src;
  img.alt = name;
  img.style.cssText = 'width:100%;border-radius:10px;display:block;max-height:70vh;object-fit:contain;background:#000';
  video.parentNode.insertBefore(img, video.nextSibling);

  meta.innerHTML = `
    <strong style="color:#f8fafc;font-size:15px">${escHtml(name)}</strong><br>
    <span style="color:#94a3b8;font-size:13px">
      🕐 ${time} &nbsp;·&nbsp; 🎯 Confidence: ${conf}% &nbsp;·&nbsp;
      <span style="color:#94a3b8;font-size:12px">🖼 Thumbnail — frame captured at highlight moment</span>
    </span>`;

  modal.classList.add('open');
}

// Override closeModalBtn to also restore video element
const _origCloseModalBtn = closeModalBtn;
function closeModalBtn() {
  const video = document.getElementById('modalVideo');
  video.style.display = '';
  const img = document.getElementById('lightboxImg');
  if (img) img.remove();
  _origCloseModalBtn && _origCloseModalBtn();
  // fallback
  const modal = document.getElementById('videoModal');
  modal.classList.remove('open');
  video.pause();
  video.src = '';
}

/* ────────────────────────────────────────
   AUDIO SPIKES CHART
──────────────────────────────────────── */
function renderSpikesChart() {
  const spikes = REPORT.audio_spikes || [];
  const ctx    = document.getElementById('spikesChart').getContext('2d');

  if (!spikes.length) {
    document.querySelector('.chart-wrap').innerHTML =
      '<div class="empty-state">No audio spikes detected.</div>';
    return;
  }

  const labels = spikes.map(s => fmtTime(s.timestamp));
  const data   = spikes.map(s => parseFloat((s.energy || 0).toFixed(4)));

  const gradient = ctx.createLinearGradient(0, 0, 0, 120);
  gradient.addColorStop(0, 'rgba(139,92,246,0.8)');
  gradient.addColorStop(1, 'rgba(139,92,246,0.05)');

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Crowd Energy',
        data,
        backgroundColor: gradient,
        borderColor: '#8b5cf6',
        borderWidth: 1,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => `⏱ ${items[0].label}`,
            label: (item)  => `Energy: ${item.raw}`
          },
          backgroundColor: '#111827',
          borderColor: '#1e2d45',
          borderWidth: 1,
          titleColor: '#f8fafc',
          bodyColor: '#94a3b8',
        }
      },
      scales: {
        x: {
          ticks: { color: '#475569', font: { size: 11 } },
          grid:  { color: '#1e2d45' }
        },
        y: {
          ticks: { color: '#475569', font: { size: 11 } },
          grid:  { color: '#1e2d45' }
        }
      }
    }
  });
}

/* ────────────────────────────────────────
   VIDEO MODAL
──────────────────────────────────────── */
function openVideoModal(src, caption, ev) {
  const modal = document.getElementById('videoModal');
  const video = document.getElementById('modalVideo');
  const meta  = document.getElementById('modalMeta');

  video.src = src;
  meta.innerHTML = `
    <strong style="color:#f8fafc;font-size:15px">${escHtml(caption)}</strong><br>
    <span style="color:#94a3b8;font-size:13px">
      🕐 ${fmtTime(ev.timestamp || 0)} &nbsp;·&nbsp;
      🎯 Confidence: ${Math.round((ev.confidence||0)*100)}%
    </span>`;

  modal.classList.add('open');
  video.load();
}

function closeModal(e) {
  if (e.target === document.getElementById('videoModal')) closeModalBtn();
}
function closeModalBtn() {
  const modal = document.getElementById('videoModal');
  const video = document.getElementById('modalVideo');
  modal.classList.remove('open');
  video.pause();
  video.src = '';
}

/* ────────────────────────────────────────
   COPILOT Q&A
──────────────────────────────────────── */
async function sendCopilot() {
  const input = document.getElementById('copilotInput');
  const msgs  = document.getElementById('copilotMessages');
  const q     = input.value.trim();
  if (!q) return;

  input.value = '';

  // User bubble
  msgs.innerHTML += `
    <div class="copilot-msg user">
      <span class="user-avatar">🧑</span>
      <span class="msg-text">${escHtml(q)}</span>
    </div>`;

  // Thinking bubble
  const thinkId = 'think_' + Date.now();
  msgs.innerHTML += `
    <div class="copilot-msg thinking" id="${thinkId}">
      <span class="bot-avatar">🤖</span>
      <span class="msg-text">Thinking…</span>
    </div>`;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const res  = await fetch('/copilot/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, video_id: VIDEO_ID })
    });
    const data = await res.json();
    const answer = data.answer || data.message || 'Sorry, I could not find an answer.';

    document.getElementById(thinkId).outerHTML = `
      <div class="copilot-msg bot">
        <span class="bot-avatar">🤖</span>
        <span class="msg-text">${escHtml(answer)}</span>
      </div>`;
  } catch (err) {
    document.getElementById(thinkId).outerHTML = `
      <div class="copilot-msg bot">
        <span class="bot-avatar">🤖</span>
        <span class="msg-text" style="color:#ef4444">Error: ${err.message}</span>
      </div>`;
  }
  msgs.scrollTop = msgs.scrollHeight;
}

/* ────────────────────────────────────────
   JSON VIEW LINKS
──────────────────────────────────────── */
function openEventsJson() {
  const w = window.open('', '_blank');
  w.document.write(`<pre style="background:#0a0e1a;color:#94a3b8;padding:20px;font-size:13px">${escHtml(JSON.stringify(REPORT?.events || [], null, 2))}</pre>`);
}
function openSummaryJson() {
  const w = window.open('', '_blank');
  w.document.write(`<pre style="background:#0a0e1a;color:#94a3b8;padding:20px;font-size:13px">${escHtml(JSON.stringify(REPORT?.match_summary || {}, null, 2))}</pre>`);
}

/* ────────────────────────────────────────
   HELPERS
──────────────────────────────────────── */
function fmtTime(sec) {
  const s = parseFloat(sec) || 0;
  const m = Math.floor(s / 60);
  const r = Math.floor(s % 60);
  return `${String(m).padStart(2,'0')}:${String(r).padStart(2,'0')}`;
}

function fmtDuration(sec) {
  const s = parseFloat(sec) || 0;
  const m = Math.floor(s / 60);
  const r = Math.floor(s % 60);
  return `${String(m).padStart(2,'0')}:${String(r).padStart(2,'0')}`;
}

function cleanSportName(sport) {
  return (sport || 'Unknown')
    .replace(/^a\s+/i,'')
    .replace(/^an\s+/i,'')
    .replace(/\bMatch\b/gi,'')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase());
}

function formatEventName(ev) {
  return (ev || 'Event')
    .replace(/_/g,' ')
    .replace(/\ba\b/gi,'')
    .replace(/\ban\b/gi,'')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase());
}

function getBasename(path) {
  if (!path) return '';
  return path.replace(/\\/g,'/').split('/').pop();
}

function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function showGlobalError(msg) {
  document.getElementById('dashPage').innerHTML =
    `<div class="section" style="text-align:center;padding:60px">
       <div style="font-size:48px;margin-bottom:16px">⚠️</div>
       <p style="color:#94a3b8;font-size:16px">${escHtml(msg)}</p>
       <a href="/" style="display:inline-block;margin-top:24px;background:#7c3aed;color:#fff;padding:12px 28px;border-radius:10px;font-weight:600">← Upload a Video</a>
     </div>`;
}
