/* ══════════════════════════════════════════
   Upload Page — JS
══════════════════════════════════════════ */

let selectedFile = null;
let currentVideoId = null;
let pollInterval = null;

const fileInput    = document.getElementById('fileInput');
const fileName     = document.getElementById('fileName');
const analyzeBtn   = document.getElementById('analyzeBtn');
const uploadProg   = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressStage= document.getElementById('progressStage');
const dropZone     = document.getElementById('dropZone');
const dashLink     = document.getElementById('dashLink');

/* ── File picker ── */
fileInput.addEventListener('change', e => {
  const f = e.target.files[0];
  if (f) selectFile(f);
});

/* ── Drag and drop ── */
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) selectFile(f);
});
dropZone.addEventListener('click', e => {
  if (e.target !== fileInput) fileInput.click();
});

function selectFile(f) {
  selectedFile = f;
  fileName.textContent = '✓ ' + f.name;
  fileName.classList.remove('none');
  fileName.style.color = '#22c55e';
}

/* ── Main flow ── */
async function runAnalysis() {
  if (!selectedFile) {
    fileName.textContent = 'Please choose a video file first.';
    fileName.style.color = '#ef4444';
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = 'Uploading…';
  uploadProg.style.display = 'flex';
  setProgress(5, 'Uploading video…');

  try {
    /* 1. Upload */
    const fd = new FormData();
    fd.append('file', selectedFile);

    const upRes = await fetch('/upload/', { method: 'POST', body: fd });
    if (!upRes.ok) throw new Error(`Upload failed: ${upRes.status}`);
    const upData = await upRes.json();
    currentVideoId = upData.video_id;

    /* Store video_id in sessionStorage for dashboard */
    sessionStorage.setItem('video_id', currentVideoId);

    setProgress(15, 'Upload complete – starting analysis…');
    analyzeBtn.textContent = 'Analyzing…';

    /* 2. Kick off analysis */
    const anRes = await fetch(`/analyze/${currentVideoId}`, { method: 'POST' });
    if (!anRes.ok) throw new Error(`Analysis start failed: ${anRes.status}`);

    /* 3. Poll progress */
    dashLink.style.display = 'inline';
    pollProgress();

  } catch (err) {
    setProgress(0, 'Error: ' + err.message);
    progressFill.style.background = '#ef4444';
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = '🚀 Analyze Match';
  }
}

function pollProgress() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const res  = await fetch(`/progress/${currentVideoId}`);
      const data = await res.json();
      const pct  = data.progress || 0;
      const stage= data.stage || 'Processing…';

      setProgress(pct, stage);

      if (pct >= 100) {
        clearInterval(pollInterval);
        setProgress(100, '✅ Analysis complete — redirecting…');
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1200);
      }

      if (stage.startsWith('Error:')) {
        clearInterval(pollInterval);
        progressFill.style.background = '#ef4444';
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '🚀 Analyze Match';
      }
    } catch (_) {}
  }, 1000);
}

function setProgress(pct, stage) {
  progressFill.style.width = pct + '%';
  progressStage.textContent = stage;
}
