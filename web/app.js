const $ = (id) => document.getElementById(id);
const LICENSE_KEY = 'pqm_license_session_v1';
const PENDING_LICENSE_KEY = 'pqm_pending_license_session_v1';
const INSTALL_KEY = 'pqm_install_id_v1';
const SAVED_KEY = 'pqm_saved_quests_v1';
let quest = null;
let currentClue = 0;
let licensed = false;
let timerSeconds = 45 * 60;
let timerHandle = null;
let score = 0;

const read = (key, fallback) => { try { const value = localStorage.getItem(key); return value === null ? fallback : JSON.parse(value); } catch (_) { return fallback; } };
const write = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* storage is optional */ } };
const remove = (key) => { try { localStorage.removeItem(key); } catch (_) { /* storage is optional */ } };
const titleCase = (value) => value.charAt(0).toUpperCase() + value.slice(1);
function installId() {
  let value = read(INSTALL_KEY, '');
  if (!value) { value = `browser_${crypto.randomUUID().replaceAll('-', '')}`; write(INSTALL_KEY, value); }
  return value;
}

function requestPayload() {
  return {
    mode: document.querySelector('input[name="mode"]:checked').value,
    occasion: $('occasion').value, age_group: $('age-group').value,
    theme: $('theme').value, location: $('location').value,
    players: Number($('players').value), difficulty: $('difficulty').value,
    minutes: Number($('minutes').value), guest_name: $('guest-name').value.trim(),
    message: $('message').value.trim(),
  };
}

function renderClue(index) {
  if (!quest) return;
  currentClue = (index + quest.clues.length) % quest.clues.length;
  const clue = quest.clues[currentClue];
  $('clue-number').textContent = clue.number; $('clue-kind').textContent = clue.kind;
  $('clue-title').textContent = clue.title; $('clue-prompt').textContent = clue.prompt;
  $('clue-location').textContent = titleCase(clue.location); $('clue-hint').textContent = clue.hint;
  $('clue-position').textContent = `${currentClue + 1} / ${quest.clues.length}`;
  $('live-number').textContent = clue.title; $('live-prompt').textContent = clue.prompt;
  document.querySelectorAll('#quest-path li').forEach((item, itemIndex) => item.classList.toggle('active', itemIndex === currentClue));
}

function renderQuest(nextQuest) {
  quest = nextQuest; currentClue = 0; timerSeconds = quest.minutes * 60; score = 0;
  $('quest-title').textContent = quest.title; $('quest-subtitle').textContent = quest.subtitle;
  $('stat-players').textContent = quest.players; $('stat-minutes').textContent = `${quest.minutes} min`;
  $('stat-difficulty').textContent = titleCase(quest.difficulty); $('stat-clues').textContent = quest.clues.length;
  $('quest-path').innerHTML = quest.clues.map((clue, index) => `<li class="${index === 0 ? 'active' : ''}"><button type="button" data-clue="${index}">${clue.number}</button><span>${clue.title}</span></li>`).join('');
  $('pack-list').innerHTML = quest.pack.map((item) => `<li>${item}</li>`).join('');
  $('safety-note').textContent = quest.safety; $('story-heading').textContent = quest.story;
  $('host-title').textContent = quest.title; $('team-score').textContent = '0';
  updateTimer(); renderClue(0);
}

async function generate() {
  const button = document.querySelector('.generate-button[type="submit"]');
  button.disabled = true; button.querySelector('span').textContent = 'Building your quest...'; $('form-error').textContent = '';
  try {
    const response = await fetch('/api/generate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(requestPayload())});
    const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Quest generation failed.');
    renderQuest(data);
  } catch (error) { $('form-error').textContent = error.message; }
  finally { button.disabled = false; button.querySelector('span').textContent = 'Generate quest'; }
}

function openPurchase(message) { $('billing-note').textContent = message || 'Secure checkout by Stripe. No subscription.'; $('purchase-dialog').showModal(); }
function savedQuests() { return read(SAVED_KEY, []); }
function updateLicenseUi() {
  $('license-badge').textContent = licensed ? 'Lifetime tools unlocked' : 'Free quest maker';
  $('license-badge').classList.toggle('active', licensed); $('upgrade-button').hidden = licensed;
  $('saved-count').textContent = savedQuests().length;
}
function updateTimer() { const minutes = String(Math.floor(timerSeconds / 60)).padStart(2, '0'); const seconds = String(timerSeconds % 60).padStart(2, '0'); $('timer').textContent = `${minutes}:${seconds}`; }
function toggleTimer() {
  if (timerHandle) { clearInterval(timerHandle); timerHandle = null; $('timer-toggle').textContent = 'Start'; return; }
  $('timer-toggle').textContent = 'Pause'; timerHandle = setInterval(() => { if (timerSeconds <= 0) return toggleTimer(); timerSeconds -= 1; updateTimer(); }, 1000);
}
async function verify(sessionId) {
  if (!sessionId) return false;
  try { const response = await fetch(`/api/entitlement?session_id=${encodeURIComponent(sessionId)}&install_id=${encodeURIComponent(installId())}`); const data = await response.json(); if (response.ok && data.active) { licensed = true; write(LICENSE_KEY, sessionId); remove(PENDING_LICENSE_KEY); return true; } } catch (_) { /* keep free mode */ }
  return false;
}

function buildPrintPack() {
  if (!quest) return;
  const escape = (value) => String(value).replace(/[&<>"']/g, (character) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  $('print-pack').innerHTML = `<section class="print-cover"><p>Party Quest Maker</p><h1>${escape(quest.title)}</h1><h2>${escape(quest.subtitle)}</h2><p>${escape(quest.story)}</p><dl><div><dt>Players</dt><dd>${quest.players}</dd></div><div><dt>Time</dt><dd>${quest.minutes} minutes</dd></div><div><dt>Difficulty</dt><dd>${escape(titleCase(quest.difficulty))}</dd></div></dl></section>${quest.clues.map((clue) => `<article class="print-clue"><span>Clue ${clue.number}</span><h2>${escape(clue.title)}</h2><p>${escape(clue.prompt)}</p><footer><b>Suggested spot:</b> ${escape(titleCase(clue.location))}<br><b>Host hint:</b> ${escape(clue.hint)}</footer></article>`).join('')}<section class="print-guide"><h2>Host guide and answer key</h2><ol>${quest.clues.map((clue) => `<li><b>${escape(clue.title)}</b>: ${escape(clue.hint)} Suggested spot: ${escape(titleCase(clue.location))}.</li>`).join('')}</ol><p>${escape(quest.safety)}</p></section><section class="print-certificate"><p>Victory certificate</p><h1>Quest completed!</h1><p>Awarded to</p><div class="certificate-line"></div><p>for completing ${escape(quest.title)}</p></section>`;
}

$('quest-form').addEventListener('submit', (event) => { event.preventDefault(); generate(); });
$('message').addEventListener('input', () => $('message-count').textContent = `${$('message').value.length} / 180`);
$('quest-path').addEventListener('click', (event) => { const button = event.target.closest('[data-clue]'); if (button) renderClue(Number(button.dataset.clue)); });
$('previous-clue').addEventListener('click', () => renderClue(currentClue - 1)); $('next-clue').addEventListener('click', () => renderClue(currentClue + 1));
$('upgrade-button').addEventListener('click', () => openPurchase()); $('close-purchase').addEventListener('click', () => $('purchase-dialog').close());
$('buy-lifetime').addEventListener('click', async () => { const button = $('buy-lifetime'); button.disabled = true; $('billing-note').textContent = 'Opening secure checkout...'; try { const response = await fetch('/api/checkout', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({install_id: installId()})}); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Checkout could not start.'); window.location.assign(data.url); } catch (error) { $('billing-note').textContent = error.message; button.disabled = false; } });
$('print-button').addEventListener('click', () => { if (!licensed) return openPurchase('Complete printable packs are included with lifetime tools.'); buildPrintPack(); window.print(); });
$('host-button').addEventListener('click', () => licensed ? $('host-dialog').showModal() : openPurchase('Host mode is included with lifetime access.'));
$('save-button').addEventListener('click', () => { if (!licensed) return openPurchase('Saved quests are included with lifetime access.'); if (!quest) return; const items = savedQuests().filter((item) => item.id !== quest.id); items.unshift(quest); write(SAVED_KEY, items.slice(0, 30)); updateLicenseUi(); $('save-button').textContent = 'Saved'; setTimeout(() => $('save-button').textContent = 'Save quest', 1000); });
$('saved-button').addEventListener('click', () => { const items = savedQuests(); $('saved-empty').hidden = items.length > 0; $('saved-list').innerHTML = items.map((item, index) => `<li><button type="button" data-saved="${index}"><span><b>${item.title}</b><br><small>${item.subtitle}</small></span><strong>${item.clues.length} clues</strong></button></li>`).join(''); $('saved-dialog').showModal(); });
$('saved-list').addEventListener('click', (event) => { const button = event.target.closest('[data-saved]'); if (!button) return; renderQuest(savedQuests()[Number(button.dataset.saved)]); $('saved-dialog').close(); }); $('close-saved').addEventListener('click', () => $('saved-dialog').close());
$('close-host').addEventListener('click', () => { if (timerHandle) toggleTimer(); $('host-dialog').close(); }); $('timer-toggle').addEventListener('click', toggleTimer); $('timer-reset').addEventListener('click', () => { if (timerHandle) toggleTimer(); timerSeconds = (quest?.minutes || 45) * 60; updateTimer(); });
$('complete-clue').addEventListener('click', () => { score += quest?.clues[currentClue].points || 10; $('team-score').textContent = score; renderClue(currentClue + 1); }); $('add-points').addEventListener('click', () => { score += 10; $('team-score').textContent = score; });

async function init() {
  installId();
  const params = new URLSearchParams(location.search);
  const returnedSession = params.get('session_id');
  if (returnedSession) write(PENDING_LICENSE_KEY, returnedSession);
  const sessionToVerify = returnedSession || read(PENDING_LICENSE_KEY, '') || read(LICENSE_KEY, '');
  const verified = await verify(sessionToVerify);
  if (params.get('checkout') === 'success') { $('checkout-message').textContent = verified ? 'Lifetime tools unlocked. Saving, complete print packs, and host mode are ready.' : 'Payment received. Access verification is still processing; refresh in a moment.'; $('checkout-message').hidden = false; }
  if (params.get('checkout') === 'cancelled') { $('checkout-message').textContent = 'Checkout was cancelled. No charge was made.'; $('checkout-message').hidden = false; }
  if (params.has('checkout') && (verified || params.get('checkout') === 'cancelled')) history.replaceState({}, '', location.pathname);
  updateLicenseUi();
  const response = await fetch('/api/generate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode:'scavenger',occasion:'Birthday Party',age_group:'Kids 8-12',theme:'space',location:'home',players:6,difficulty:'medium',minutes:45,guest_name:'Jordan',message:''})});
  if (response.ok) renderQuest(await response.json());
}
init();
