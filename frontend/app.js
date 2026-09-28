/* ═══════════════════════════════════════════════════════════
   Registre IP Canada — Frontend SPA
   ═══════════════════════════════════════════════════════════ */

const API = '/api';

// ── Auth state ──────────────────────────────────────────────
let token = localStorage.getItem('jwt') || null;
let currentUser = null;
let currentSection = 'dashboard';

// ── Toast ───────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3800);
}

// ── Fetch wrapper ───────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const r = await fetch(API + path, { ...opts, headers });
  if (r.status === 401) { logout(); return null; }
  if (!r.ok) {
    let msg = `Erreur ${r.status}`;
    try { const d = await r.json(); msg = d.detail || JSON.stringify(d); } catch {}
    toast(msg, 'error');
    return null;
  }
  return r.status === 204 ? true : r.json();
}

// ── Login ────────────────────────────────────────────────────
const loginScreen = document.getElementById('login-screen');
const appEl = document.getElementById('app');

document.getElementById('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const errEl = document.getElementById('login-error');
  const spinEl = document.getElementById('login-spinner');
  const btnTxt = document.getElementById('login-btn-text');
  errEl.classList.add('hidden');
  spinEl.classList.remove('hidden');
  btnTxt.textContent = '';

  const fd = new FormData();
  fd.append('username', document.getElementById('username').value);
  fd.append('password', document.getElementById('password').value);

  try {
    const r = await fetch(API + '/auth/login', { method: 'POST', body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Identifiants invalides');
    token = data.access_token;
    localStorage.setItem('jwt', token);
    await initApp();
  } catch(err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  } finally {
    spinEl.classList.add('hidden');
    btnTxt.textContent = 'Se connecter';
  }
});

// ── Logout ───────────────────────────────────────────────────
function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem('jwt');
  appEl.classList.add('hidden');
  loginScreen.classList.remove('hidden');
  toast('Déconnecté', 'info');
}
document.getElementById('logout-btn').addEventListener('click', logout);

// ── Init app ─────────────────────────────────────────────────
async function initApp() {
  currentUser = await apiFetch('/auth/me');
  if (!currentUser) return;
  document.getElementById('user-name').textContent = currentUser.username;
  document.getElementById('user-avatar').textContent = currentUser.username[0].toUpperCase();
  const roleLabels = { admin: 'Administrateur', agent: 'Agent OPIC', viewer: 'Lecteur' };
  document.getElementById('user-role').textContent = roleLabels[currentUser.role] || currentUser.role;

  loginScreen.classList.add('hidden');
  appEl.classList.remove('hidden');

  // Show "Nouveau" button for non-viewers
  if (currentUser.role !== 'viewer') {
    document.getElementById('btn-new').classList.remove('hidden');
  }

  navigateTo('dashboard');
}

// ── Navigation ───────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    navigateTo(item.dataset.section);
    // Close sidebar on mobile
    document.getElementById('sidebar').classList.remove('open');
  });
});

document.getElementById('menu-toggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

const sectionTitles = {
  dashboard: 'Tableau de bord',
  patents: 'Brevets',
  trademarks: 'Marques de commerce',
  copyrights: "Droits d'auteur",
  designs: 'Dessins industriels',
  search: 'Recherche globale'
};

const newBtnLabels = {
  patents: '+ Nouveau brevet',
  trademarks: '+ Nouvelle marque',
  copyrights: "+ Nouveau droit d'auteur",
  designs: '+ Nouveau dessin'
};

function navigateTo(section) {
  currentSection = section;
  // Update active nav
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.section === section));
  // Update sections visibility
  document.querySelectorAll('.section').forEach(s => s.classList.toggle('hidden', s.id !== `section-${section}`));
  // Topbar
  document.getElementById('topbar-title').textContent = sectionTitles[section] || section;
  // New button
  const btnNew = document.getElementById('btn-new');
  if (newBtnLabels[section] && currentUser?.role !== 'viewer') {
    btnNew.textContent = newBtnLabels[section];
    btnNew.classList.remove('hidden');
  } else {
    btnNew.classList.add('hidden');
  }
  // Load section data
  const loaders = { dashboard, patents, trademarks, copyrights, designs };
  if (loaders[section]) loaders[section]();
}

// ── Badge ────────────────────────────────────────────────────
function badge(status) {
  const labels = {
    draft:'Brouillon', filed:'Déposé', published:'Publié', granted:'Accordé',
    registered:'Enregistré', advertised:'Annoncé', refused:'Refusé',
    rejected:'Rejeté', abandoned:'Abandonné', expired:'Expiré', active:'Actif'
  };
  const s = status || 'draft';
  return `<span class="badge badge-${s}">${labels[s] || s}</span>`;
}

function fmtDate(d) { return d ? new Date(d).toLocaleDateString('fr-CA') : '—'; }
function esc(s) { if (!s) return '—'; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

// ═══════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════
async function dashboard() {
  const [patents, trademarks, copyrights, designs] = await Promise.all([
    apiFetch('/patents'), apiFetch('/trademarks'), apiFetch('/copyrights'), apiFetch('/designs')
  ]);
  if (!patents) return;

  document.getElementById('stat-patents').textContent = patents.length;
  document.getElementById('stat-trademarks').textContent = trademarks?.length ?? '—';
  document.getElementById('stat-copyrights').textContent = copyrights?.length ?? '—';
  document.getElementById('stat-designs').textContent = designs?.length ?? '—';

  renderRecentPatents(patents.slice(0, 5));
  renderRecentTrademarks((trademarks || []).slice(0, 5));
}

function renderRecentPatents(items) {
  const el = document.getElementById('recent-patents');
  if (!items.length) { el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⚙</div><div class="empty-state-text">Aucun brevet</div></div>'; return; }
  el.innerHTML = items.map(p => `
    <div class="recent-item">
      <div class="recent-name">${esc(p.title_fr || p.title_en || '—')}</div>
      <div class="recent-meta">${badge(p.status)}</div>
    </div>`).join('');
}

function renderRecentTrademarks(items) {
  const el = document.getElementById('recent-trademarks');
  if (!items.length) { el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">™</div><div class="empty-state-text">Aucune marque</div></div>'; return; }
  el.innerHTML = items.map(t => `
    <div class="recent-item">
      <div class="recent-name">${esc(t.name_fr || t.name_en || t.mark_text || '—')}</div>
      <div class="recent-meta">${badge(t.status)}</div>
    </div>`).join('');
}

// ═══════════════════════════════════════════════
// PATENTS
// ═══════════════════════════════════════════════
let allPatents = [];

async function patents() {
  const data = await apiFetch('/patents');
  if (!data) return;
  allPatents = data;
  renderPatents(allPatents);
}

function renderPatents(items) {
  const tbody = document.getElementById('tbody-patents');
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">⚙</div><div class="empty-state-text">Aucun brevet enregistré</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = items.map(p => `
    <tr>
      <td>${p.id}</td>
      <td><strong>${esc(p.title_fr)}</strong>${p.title_en ? `<br><small style="color:var(--slate-4)">${esc(p.title_en)}</small>` : ''}</td>
      <td>${esc(p.applicant)}</td>
      <td><span style="text-transform:capitalize">${p.patent_type || '—'}</span></td>
      <td>${badge(p.status)}</td>
      <td>${fmtDate(p.filing_date)}</td>
      <td><button class="btn-view" onclick="showPatent(${p.id})">Voir</button></td>
    </tr>`).join('');
}

document.getElementById('filter-patents').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  const status = document.getElementById('filter-patent-status').value;
  renderPatents(allPatents.filter(p =>
    (!q || (p.title_fr||'').toLowerCase().includes(q) || (p.title_en||'').toLowerCase().includes(q)) &&
    (!status || p.status === status)
  ));
});
document.getElementById('filter-patent-status').addEventListener('change', e => {
  const ev = new Event('input'); document.getElementById('filter-patents').dispatchEvent(ev);
});

async function showPatent(id) {
  const p = await apiFetch(`/patents/${id}`);
  if (!p) return;
  const typeLabels = { utility:'Utilité', design:'Dessin', plant:'Plante' };
  showModal(`Brevet #${p.id}`, `
    <div class="detail-grid">
      <div class="detail-field detail-full">
        <div class="detail-label">Titre (FR)</div>
        <div class="detail-value">${esc(p.title_fr)}</div>
      </div>
      ${p.title_en ? `<div class="detail-field detail-full"><div class="detail-label">Title (EN)</div><div class="detail-value">${esc(p.title_en)}</div></div>` : ''}
      <hr class="detail-divider">
      <div class="detail-field">
        <div class="detail-label">Statut</div>
        <div class="detail-value">${badge(p.status)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Type</div>
        <div class="detail-value">${typeLabels[p.patent_type] || p.patent_type || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">N° demande</div>
        <div class="detail-value mono">${p.application_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">N° brevet</div>
        <div class="detail-value mono">${p.patent_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">PCT</div>
        <div class="detail-value mono">${p.pct_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Date de dépôt</div>
        <div class="detail-value">${fmtDate(p.filing_date)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Date d'octroi</div>
        <div class="detail-value">${fmtDate(p.grant_date)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Expiration</div>
        <div class="detail-value">${fmtDate(p.expiry_date)}</div>
      </div>
      ${p.inventors ? `<div class="detail-field detail-full"><div class="detail-label">Inventeurs</div><div class="detail-value">${esc(JSON.stringify(p.inventors))}</div></div>` : ''}
      ${p.ipc_codes ? `<div class="detail-field detail-full"><div class="detail-label">Codes IPC</div><div class="detail-value mono">${esc(JSON.stringify(p.ipc_codes))}</div></div>` : ''}
      <div class="detail-field detail-full">
        <div class="detail-label">Créé le</div>
        <div class="detail-value">${fmtDate(p.created_at)}</div>
      </div>
    </div>`, false);
}

function showNewPatentForm() {
  showModal('Nouveau brevet', `
    <div class="form-row">
      <div class="form-group">
        <label>Titre (FR) *</label>
        <input type="text" id="f-title-fr" placeholder="ex. Procédé de fabrication…" required/>
      </div>
      <div class="form-group">
        <label>Title (EN)</label>
        <input type="text" id="f-title-en" placeholder="ex. Manufacturing process…"/>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Déposant *</label>
        <input type="text" id="f-applicant" placeholder="Nom de l'entreprise ou personne"/>
      </div>
      <div class="form-group">
        <label>Type</label>
        <select id="f-type">
          <option value="utility">Utilité</option>
          <option value="design">Dessin</option>
          <option value="plant">Plante</option>
        </select>
      </div>
    </div>
    <div class="form-group">
      <label>Abrégé (FR)</label>
      <textarea id="f-abstract" placeholder="Description courte de l'invention…"></textarea>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>N° demande OPIC</label>
        <input type="text" id="f-appnum" placeholder="ex. CA3012345"/>
      </div>
      <div class="form-group">
        <label>Date de dépôt</label>
        <input type="date" id="f-filingdate"/>
      </div>
    </div>
  `, true, async () => {
    const title_fr = document.getElementById('f-title-fr').value.trim();
    if (!title_fr) { toast('Le titre FR est requis', 'error'); return false; }
    const body = {
      title_fr, title_en: document.getElementById('f-title-en').value || null,
      patent_type: document.getElementById('f-type').value,
      abstract_fr: document.getElementById('f-abstract').value || null,
      application_number: document.getElementById('f-appnum').value || null,
      filing_date: document.getElementById('f-filingdate').value || null,
    };
    // Applicant is set on the model via applicant field (not in schema — just title+type needed)
    const result = await apiFetch('/patents', { method: 'POST', body: JSON.stringify(body) });
    if (result) { toast('Brevet créé avec succès', 'success'); patents(); return true; }
    return false;
  });
}

// ═══════════════════════════════════════════════
// TRADEMARKS
// ═══════════════════════════════════════════════
let allTrademarks = [];

async function trademarks() {
  const data = await apiFetch('/trademarks');
  if (!data) return;
  allTrademarks = data;
  renderTrademarks(allTrademarks);
}

function renderTrademarks(items) {
  const tbody = document.getElementById('tbody-trademarks');
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">™</div><div class="empty-state-text">Aucune marque enregistrée</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = items.map(t => {
    const classes = t.nice_classes ? t.nice_classes.map(c => c.class || c).join(', ') : '—';
    const name = t.name_fr || t.name_en || t.mark_text || '—';
    return `<tr>
      <td>${t.id}</td>
      <td><strong>${esc(name)}</strong>${t.name_en && t.name_fr ? `<br><small style="color:var(--slate-4)">${esc(t.name_en)}</small>` : ''}</td>
      <td>${esc(t.owner || '—')}</td>
      <td><span style="text-transform:capitalize">${t.trademark_type || '—'}</span></td>
      <td>${esc(classes)}</td>
      <td>${badge(t.status)}</td>
      <td><button class="btn-view" onclick="showTrademark(${t.id})">Voir</button></td>
    </tr>`;
  }).join('');
}

document.getElementById('filter-trademarks').addEventListener('input', () => filterTrademarks());
document.getElementById('filter-tm-status').addEventListener('change', () => filterTrademarks());
function filterTrademarks() {
  const q = document.getElementById('filter-trademarks').value.toLowerCase();
  const status = document.getElementById('filter-tm-status').value;
  renderTrademarks(allTrademarks.filter(t =>
    (!q || (t.name_fr||'').toLowerCase().includes(q) || (t.name_en||'').toLowerCase().includes(q)) &&
    (!status || t.status === status)
  ));
}

async function showTrademark(id) {
  const t = await apiFetch(`/trademarks/${id}`);
  if (!t) return;
  const classes = t.nice_classes ? t.nice_classes.map(c => `Cl.${c.class}${c.description ? ' – ' + c.description : ''}`).join('<br>') : '—';
  showModal(`Marque #${t.id}`, `
    <div class="detail-grid">
      <div class="detail-field">
        <div class="detail-label">Nom (FR)</div>
        <div class="detail-value">${esc(t.name_fr || '—')}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Name (EN)</div>
        <div class="detail-value">${esc(t.name_en || '—')}</div>
      </div>
      <hr class="detail-divider">
      <div class="detail-field">
        <div class="detail-label">Statut</div>
        <div class="detail-value">${badge(t.status)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Type</div>
        <div class="detail-value" style="text-transform:capitalize">${t.trademark_type || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">N° demande</div>
        <div class="detail-value mono">${t.application_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">N° enregistrement</div>
        <div class="detail-value mono">${t.registration_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Madrid (OMPI)</div>
        <div class="detail-value mono">${t.madrid_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Propriétaire</div>
        <div class="detail-value">${esc(t.owner || '—')}</div>
      </div>
      <div class="detail-field detail-full">
        <div class="detail-label">Classes Nice</div>
        <div class="detail-value">${classes}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Date de dépôt</div>
        <div class="detail-value">${fmtDate(t.filing_date)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Date d'enregistrement</div>
        <div class="detail-value">${fmtDate(t.registration_date)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Expiration</div>
        <div class="detail-value">${fmtDate(t.expiry_date)}</div>
      </div>
    </div>`, false);
}

function showNewTrademarkForm() {
  showModal('Nouvelle marque', `
    <div class="form-row">
      <div class="form-group">
        <label>Nom (FR) *</label>
        <input type="text" id="f-name-fr" placeholder="ex. Feuille d'érable"/>
      </div>
      <div class="form-group">
        <label>Name (EN)</label>
        <input type="text" id="f-name-en" placeholder="ex. Maple Leaf"/>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Propriétaire *</label>
        <input type="text" id="f-owner" placeholder="Nom du propriétaire"/>
      </div>
      <div class="form-group">
        <label>Type</label>
        <select id="f-tm-type">
          <option value="word">Verbale</option>
          <option value="design">Figurative</option>
          <option value="combined">Mixte</option>
          <option value="sound">Sonore</option>
          <option value="colour">Couleur</option>
          <option value="3d">3D</option>
          <option value="certification">Certification</option>
          <option value="collective">Collective</option>
        </select>
      </div>
    </div>
    <div class="form-group">
      <label>Classes Nice (ex: 9, 42)</label>
      <input type="text" id="f-classes" placeholder="Entrez les numéros séparés par des virgules"/>
    </div>
    <div class="form-group">
      <label>Description (FR)</label>
      <textarea id="f-desc-fr" placeholder="Description des produits/services couverts…"></textarea>
    </div>
  `, true, async () => {
    const name_fr = document.getElementById('f-name-fr').value.trim();
    const owner = document.getElementById('f-owner').value.trim();
    if (!name_fr) { toast('Le nom FR est requis', 'error'); return false; }
    const classesRaw = document.getElementById('f-classes').value;
    const nice_classes = classesRaw.split(',').map(s => s.trim()).filter(Boolean).map(n => ({ class: parseInt(n) || n }));
    const body = {
      name_fr, name_en: document.getElementById('f-name-en').value || null,
      owner: owner || null,
      trademark_type: document.getElementById('f-tm-type').value,
      nice_classes: nice_classes.length ? nice_classes : null,
      description_fr: document.getElementById('f-desc-fr').value || null,
    };
    const result = await apiFetch('/trademarks', { method: 'POST', body: JSON.stringify(body) });
    if (result) { toast('Marque créée avec succès', 'success'); trademarks(); return true; }
    return false;
  });
}

// ═══════════════════════════════════════════════
// COPYRIGHTS
// ═══════════════════════════════════════════════
let allCopyrights = [];

async function copyrights() {
  const data = await apiFetch('/copyrights');
  if (!data) return;
  allCopyrights = data;
  renderCopyrights(allCopyrights);
}

const workTypeLabels = {
  literary:'Littéraire', artistic:'Artistique', musical:'Musical',
  dramatic:'Dramatique', sound_recording:'Enreg. sonore',
  performance:'Représentation', communication_signal:'Signal comm.'
};

function renderCopyrights(items) {
  const tbody = document.getElementById('tbody-copyrights');
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">©</div><div class="empty-state-text">Aucun droit d'auteur enregistré</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = items.map(c => {
    const authors = c.authors ? c.authors.map(a => a.name || a).join(', ') : '—';
    return `<tr>
      <td>${c.id}</td>
      <td><strong>${esc(c.title)}</strong></td>
      <td>${workTypeLabels[c.work_type] || c.work_type || '—'}</td>
      <td>${esc(authors)}</td>
      <td>${badge(c.status)}</td>
      <td>${c.registration_number ? `<span class="detail-value mono" style="font-size:12px">${esc(c.registration_number)}</span>` : '—'}</td>
      <td><button class="btn-view" onclick="showCopyright(${c.id})">Voir</button></td>
    </tr>`;
  }).join('');
}

document.getElementById('filter-copyrights').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  const type = document.getElementById('filter-cr-type').value;
  renderCopyrights(allCopyrights.filter(c =>
    (!q || (c.title||'').toLowerCase().includes(q)) &&
    (!type || c.work_type === type)
  ));
});
document.getElementById('filter-cr-type').addEventListener('change', () => {
  const ev = new Event('input'); document.getElementById('filter-copyrights').dispatchEvent(ev);
});

async function showCopyright(id) {
  const c = await apiFetch(`/copyrights/${id}`);
  if (!c) return;
  const authors = c.authors ? c.authors.map(a => a.name || JSON.stringify(a)).join(', ') : '—';
  showModal(`Droit d'auteur #${c.id}`, `
    <div class="detail-grid">
      <div class="detail-field detail-full">
        <div class="detail-label">Titre</div>
        <div class="detail-value">${esc(c.title)}</div>
      </div>
      <hr class="detail-divider">
      <div class="detail-field">
        <div class="detail-label">Type d'œuvre</div>
        <div class="detail-value">${workTypeLabels[c.work_type] || c.work_type || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Statut</div>
        <div class="detail-value">${badge(c.status)}</div>
      </div>
      <div class="detail-field detail-full">
        <div class="detail-label">Auteur(s)</div>
        <div class="detail-value">${esc(authors)}</div>
      </div>
      ${c.owners ? `<div class="detail-field detail-full"><div class="detail-label">Titulaires</div><div class="detail-value">${esc(JSON.stringify(c.owners))}</div></div>` : ''}
      <div class="detail-field">
        <div class="detail-label">N° enregistrement</div>
        <div class="detail-value mono">${c.registration_number || '—'}</div>
      </div>
      ${c.description ? `<div class="detail-field detail-full"><div class="detail-label">Description</div><div class="detail-value">${esc(c.description)}</div></div>` : ''}
    </div>`, false);
}

function showNewCopyrightForm() {
  showModal("Nouveau droit d'auteur", `
    <div class="form-group">
      <label>Titre de l'œuvre *</label>
      <input type="text" id="f-cr-title" placeholder="ex. Logiciel de détection…"/>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Type d'œuvre</label>
        <select id="f-cr-type">
          <option value="literary">Littéraire</option>
          <option value="artistic">Artistique</option>
          <option value="musical">Musical</option>
          <option value="dramatic">Dramatique</option>
          <option value="sound_recording">Enregistrement sonore</option>
          <option value="performance">Représentation</option>
          <option value="communication_signal">Signal de communication</option>
        </select>
      </div>
      <div class="form-group">
        <label>Auteur principal</label>
        <input type="text" id="f-cr-author" placeholder="Prénom Nom"/>
      </div>
    </div>
    <div class="form-group">
      <label>Description</label>
      <textarea id="f-cr-desc" placeholder="Description de l'œuvre…"></textarea>
    </div>
  `, true, async () => {
    const title = document.getElementById('f-cr-title').value.trim();
    if (!title) { toast("Le titre est requis", 'error'); return false; }
    const authorName = document.getElementById('f-cr-author').value.trim();
    const body = {
      title,
      work_type: document.getElementById('f-cr-type').value,
      authors: authorName ? [{ name: authorName }] : null,
      description: document.getElementById('f-cr-desc').value || null,
    };
    const result = await apiFetch('/copyrights', { method: 'POST', body: JSON.stringify(body) });
    if (result) { toast("Droit d'auteur créé", 'success'); copyrights(); return true; }
    return false;
  });
}

// ═══════════════════════════════════════════════
// DESIGNS
// ═══════════════════════════════════════════════
let allDesigns = [];

async function designs() {
  const data = await apiFetch('/designs');
  if (!data) return;
  allDesigns = data;
  renderDesigns(allDesigns);
}

function renderDesigns(items) {
  const tbody = document.getElementById('tbody-designs');
  if (!items.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="empty-state-icon">◈</div><div class="empty-state-text">Aucun dessin industriel enregistré</div></div></td></tr>`;
    return;
  }
  tbody.innerHTML = items.map(d => {
    const classes = d.locarno_classes ? d.locarno_classes.join(', ') : '—';
    return `<tr>
      <td>${d.id}</td>
      <td><strong>${esc(d.title)}</strong></td>
      <td>${esc(d.owner || '—')}</td>
      <td>${esc(classes)}</td>
      <td>${badge(d.status)}</td>
      <td>${fmtDate(d.filing_date)}</td>
      <td><button class="btn-view" onclick="showDesign(${d.id})">Voir</button></td>
    </tr>`;
  }).join('');
}

document.getElementById('filter-designs').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  renderDesigns(allDesigns.filter(d => (!q || (d.title||'').toLowerCase().includes(q))));
});

async function showDesign(id) {
  const d = await apiFetch(`/designs/${id}`);
  if (!d) return;
  showModal(`Dessin industriel #${d.id}`, `
    <div class="detail-grid">
      <div class="detail-field detail-full">
        <div class="detail-label">Titre</div>
        <div class="detail-value">${esc(d.title)}</div>
      </div>
      ${d.article_name ? `<div class="detail-field detail-full"><div class="detail-label">Nom de l'article</div><div class="detail-value">${esc(d.article_name)}</div></div>` : ''}
      <hr class="detail-divider">
      <div class="detail-field">
        <div class="detail-label">Statut</div>
        <div class="detail-value">${badge(d.status)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Propriétaire</div>
        <div class="detail-value">${esc(d.owner || '—')}</div>
      </div>
      ${d.locarno_classes ? `<div class="detail-field detail-full"><div class="detail-label">Classes Locarno</div><div class="detail-value mono">${esc(d.locarno_classes.join(', '))}</div></div>` : ''}
      <div class="detail-field">
        <div class="detail-label">N° demande</div>
        <div class="detail-value mono">${d.application_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">N° enregistrement</div>
        <div class="detail-value mono">${d.registration_number || '—'}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Date de dépôt</div>
        <div class="detail-value">${fmtDate(d.filing_date)}</div>
      </div>
      <div class="detail-field">
        <div class="detail-label">Date d'enregistrement</div>
        <div class="detail-value">${fmtDate(d.registration_date)}</div>
      </div>
    </div>`, false);
}

function showNewDesignForm() {
  showModal('Nouveau dessin industriel', `
    <div class="form-group">
      <label>Titre *</label>
      <input type="text" id="f-ds-title" placeholder="ex. Interface utilisateur du téléphone…"/>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Propriétaire *</label>
        <input type="text" id="f-ds-owner" placeholder="Nom de l'entreprise ou personne"/>
      </div>
      <div class="form-group">
        <label>Nom de l'article</label>
        <input type="text" id="f-ds-article" placeholder="ex. Téléphone mobile"/>
      </div>
    </div>
    <div class="form-group">
      <label>Classes Locarno (ex: 14-04, 14-99)</label>
      <input type="text" id="f-ds-locarno" placeholder="Séparées par des virgules"/>
    </div>
    <div class="form-group">
      <label>Date de dépôt</label>
      <input type="date" id="f-ds-filing"/>
    </div>
  `, true, async () => {
    const title = document.getElementById('f-ds-title').value.trim();
    const owner = document.getElementById('f-ds-owner').value.trim();
    if (!title) { toast('Le titre est requis', 'error'); return false; }
    const locarnoRaw = document.getElementById('f-ds-locarno').value;
    const locarno_classes = locarnoRaw.split(',').map(s => s.trim()).filter(Boolean);
    const body = {
      title, owner: owner || null,
      article_name: document.getElementById('f-ds-article').value || null,
      locarno_classes: locarno_classes.length ? locarno_classes : null,
      filing_date: document.getElementById('f-ds-filing').value || null,
    };
    const result = await apiFetch('/designs', { method: 'POST', body: JSON.stringify(body) });
    if (result) { toast('Dessin industriel créé', 'success'); designs(); return true; }
    return false;
  });
}

// ═══════════════════════════════════════════════
// SEARCH
// ═══════════════════════════════════════════════
async function performSearch() {
  const q = document.getElementById('global-search-input').value.trim();
  const container = document.getElementById('search-results');
  if (!q) { container.innerHTML = ''; return; }

  container.innerHTML = '<div class="loading-row"></div>';
  const results = await apiFetch(`/search?q=${encodeURIComponent(q)}`);
  if (!results) { container.innerHTML = ''; return; }
  if (!results.length) {
    container.innerHTML = `<div class="search-empty"><div class="search-empty-icon">⌕</div><div>Aucun résultat pour "<strong>${esc(q)}</strong>"</div></div>`;
    return;
  }

  const typeIcons = { patent:'⚙', trademark:'™', copyright:'©', design:'◈' };
  const typeLabels = { patent:'Brevet', trademark:'Marque', copyright:"Droit d'auteur", design:'Dessin industriel' };
  container.innerHTML = results.map(r => `
    <div class="search-result-item result-type-${r.type}">
      <div class="result-icon">${typeIcons[r.type] || '•'}</div>
      <div class="result-body">
        <div class="result-title">${esc(r.title)}</div>
        <div class="result-meta">${typeLabels[r.type] || r.type} · #${r.id} · ${badge(r.status)}</div>
      </div>
    </div>`).join('');
}

document.getElementById('global-search-btn').addEventListener('click', performSearch);
document.getElementById('global-search-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') performSearch();
});

// ═══════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════
let modalSubmitCallback = null;

function showModal(title, bodyHTML, hasForm = false, onSubmit = null) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHTML;
  const footer = document.getElementById('modal-footer');
  const submitBtn = document.getElementById('modal-submit');
  submitBtn.style.display = hasForm ? '' : 'none';
  modalSubmitCallback = onSubmit;
  document.getElementById('modal-overlay').classList.remove('hidden');
  // Focus first input
  setTimeout(() => {
    const first = document.querySelector('#modal-body input, #modal-body select, #modal-body textarea');
    if (first) first.focus();
  }, 80);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.getElementById('modal-body').innerHTML = '';
  modalSubmitCallback = null;
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-cancel').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});

document.getElementById('modal-submit').addEventListener('click', async () => {
  if (!modalSubmitCallback) return;
  const btn = document.getElementById('modal-submit');
  btn.disabled = true;
  btn.textContent = 'Enregistrement…';
  const success = await modalSubmitCallback();
  btn.disabled = false;
  btn.textContent = 'Enregistrer';
  if (success) closeModal();
});

// ── "Nouveau" button routes ──────────────────────
document.getElementById('btn-new').addEventListener('click', () => {
  const actions = {
    patents: showNewPatentForm,
    trademarks: showNewTrademarkForm,
    copyrights: showNewCopyrightForm,
    designs: showNewDesignForm,
  };
  if (actions[currentSection]) actions[currentSection]();
});

// Expose view functions globally (called from inline onclick)
window.showPatent = showPatent;
window.showTrademark = showTrademark;
window.showCopyright = showCopyright;
window.showDesign = showDesign;

// ═══════════════════════════════════════════════
// BOOT
// ═══════════════════════════════════════════════
(async () => {
  if (token) {
    // Try to restore session
    const user = await apiFetch('/auth/me');
    if (user) {
      currentUser = user;
      document.getElementById('user-name').textContent = user.username;
      document.getElementById('user-avatar').textContent = user.username[0].toUpperCase();
      const roleLabels = { admin: 'Administrateur', agent: 'Agent OPIC', viewer: 'Lecteur' };
      document.getElementById('user-role').textContent = roleLabels[user.role] || user.role;
      if (user.role !== 'viewer') document.getElementById('btn-new').classList.remove('hidden');
      loginScreen.classList.add('hidden');
      appEl.classList.remove('hidden');
      navigateTo('dashboard');
    }
  }
})();
