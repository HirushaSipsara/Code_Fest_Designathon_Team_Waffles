import { useLayoutEffect, useRef } from 'react';
import prototypeDocument from '../../livlink-prototype.html?raw';
import polishStyles from './polish.css?inline';
import { confirmScene, parseScene, simulateArrival, type Device, type Proposal } from './api';

const styleText = prototypeDocument.match(/<style>([\s\S]*?)<\/style>/i)?.[1] ?? '';
const bodyMarkup = prototypeDocument.match(/<body>([\s\S]*?)<script>/i)?.[1] ?? '';
const prototypeScript = prototypeDocument.match(/<script>([\s\S]*?)<\/script>/i)?.[1] ?? '';

declare global {
  interface Window {
    toast?: (message: string) => void;
    logActivity?: (message: string, category?: string) => void;
  }
}

function escapeHtml(value: unknown) {
  return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]!);
}

function currentRole() {
  return document.querySelector<HTMLButtonElement>('#rolePill button.active')?.dataset.role || 'owner';
}

function deviceName(actionDeviceId: string, devices: Device[]) {
  const device = devices.find(item => item.id === actionDeviceId);
  return device ? `${device.room} ${device.name}` : actionDeviceId;
}

function actionLabel(proposal: Proposal, devices: Device[]) {
  return proposal.actions.map(action => {
    const suffix = action.value == null ? '' : action.action === 'set_temperature' ? ` → ${action.value}°C` : ` → ${action.value}%`;
    return `${deviceName(action.device_id, devices)} · ${action.action.replace(/_/g, ' ')}${suffix}`;
  });
}

function renderFallback(host: HTMLElement, proposal: Proposal) {
  host.innerHTML = `<div class="card tight" style="background:var(--surface-2);">
    <div class="row between"><b style="font-size:15px;">AI scene creation is ${escapeHtml(proposal.status.replace(/_/g, ' '))}.</b><span class="tag tag-sim"><span class="dot"></span>${escapeHtml(proposal.status)}</span></div>
    <p class="fine" style="margin-top:6px;">${escapeHtml(proposal.reason || proposal.explanation)}</p>
    <button class="btn btn-ghost btn-sm" id="backendManualBuilder">Use the visual scene builder</button>
  </div>`;
  document.querySelector('#backendManualBuilder')?.addEventListener('click', () => document.querySelector('#dndPalette')?.scrollIntoView({ behavior: 'smooth', block: 'center' }));
}

function renderProposal(host: HTMLElement, proposal: Proposal, devices: Device[]) {
  const actions = actionLabel(proposal, devices);
  host.innerHTML = `<div class="card tight" style="background:var(--accent-soft);border-color:transparent;">
    <div class="row between"><b style="font-size:15.5px;">Proposed: ${escapeHtml(proposal.scene_name)}</b><span class="tag tag-build"><span class="dot"></span>validated draft</span></div>
    <div class="stack" style="gap:5px;margin:10px 0;">
      <div class="fine"><b>WHEN</b> resident arrives</div>
      <div class="fine"><b>IF</b> ${proposal.conditions.length ? escapeHtml(proposal.conditions.map(item => `time is after ${item.value}`).join(' and ')) : 'no condition'}</div>
      ${actions.map(action => `<div class="fine">• ${escapeHtml(action)}</div>`).join('')}
    </div>
    <p class="fine">${escapeHtml(proposal.explanation)}</p>
    <p class="fine" style="color:var(--success);font-weight:700;">✓ Devices recognised &nbsp; ✓ Values valid &nbsp; ✓ Permission allowed</p>
    <div class="row" style="gap:8px;flex-wrap:wrap;">
      <button class="btn btn-primary btn-sm" id="backendConfirmScene">Confirm &amp; Save</button>
      <button class="btn btn-ghost btn-sm" id="backendEditScene">Edit in visual builder</button>
    </div>
  </div>`;
  document.querySelector('#backendEditScene')?.addEventListener('click', () => document.querySelector('#dndPalette')?.scrollIntoView({ behavior: 'smooth', block: 'center' }));
  document.querySelector('#backendConfirmScene')?.addEventListener('click', async event => {
    const button = event.currentTarget as HTMLButtonElement;
    button.disabled = true;
    button.textContent = 'Saving…';
    try {
      const saved = await confirmScene(proposal, currentRole());
      button.textContent = 'Saved';
      window.toast?.(`${saved.name} confirmed and stored in PostgreSQL`);
      window.logActivity?.(`Scene confirmed — ${saved.name} (backend id ${saved.id})`, 'ok');
      const controls = button.parentElement;
      controls?.insertAdjacentHTML('beforeend', '<button class="btn btn-ghost btn-sm" id="backendArrival">SIMULATION ONLY · Simulate Resident Arrival</button>');
      document.querySelector('#backendArrival')?.addEventListener('click', async arrivalEvent => {
        const arrivalButton = arrivalEvent.currentTarget as HTMLButtonElement;
        arrivalButton.disabled = true;
        arrivalButton.textContent = 'Requested…';
        try {
          const response = await simulateArrival();
          const results = response.executions.flatMap(item => item.results);
          arrivalButton.textContent = results.length ? 'Acknowledged' : 'No matching scene';
          window.toast?.(results.length ? `Requested → Acknowledged by ${results.length} simulated device${results.length === 1 ? '' : 's'}` : 'No confirmed scene matched the current time');
          window.logActivity?.(`Simulated arrival — ${results.length} device acknowledgement${results.length === 1 ? '' : 's'}`, results.length ? 'ok' : 'warn');
        } catch (error) {
          arrivalButton.disabled = false;
          arrivalButton.textContent = 'Simulation failed · retry';
          window.toast?.(error instanceof Error ? error.message : 'Arrival simulation failed');
        }
      });
    } catch (error) {
      button.disabled = false;
      button.textContent = 'Confirm & Save';
      window.toast?.(error instanceof Error ? error.message : 'Scene confirmation failed');
    }
  });
}

function wireBackendSceneComposer() {
  const input = document.querySelector<HTMLInputElement>('#nlInput');
  const result = document.querySelector<HTMLElement>('#nlResult');
  const oldSubmit = document.querySelector<HTMLButtonElement>('#nlSubmit');
  if (!input || !result || !oldSubmit) return;

  const submit = oldSubmit.cloneNode(true) as HTMLButtonElement;
  oldSubmit.replaceWith(submit); // removes the prototype's fixed NL_MAP click listener
  const headingTag = submit.closest('.card')?.querySelector<HTMLElement>('.section-head .tag');
  if (headingTag) headingTag.innerHTML = '<span class="dot"></span>Backend AI';

  const run = async (text: string) => {
    if (!text.trim()) { window.toast?.('Describe the scene you want first'); return; }
    submit.disabled = true;
    submit.textContent = 'Interpreting…';
    result.innerHTML = '<div class="card tight" style="background:var(--surface-2);"><b>LIVLINK is interpreting your request…</b><p class="fine" style="margin-top:6px;">The request is being validated by FastAPI. No device will run without confirmation.</p></div>';
    try {
      const [proposal, deviceResponse] = await Promise.all([parseScene(text, currentRole()), fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/devices`).then(response => response.json())]);
      if (proposal.status === 'ready') renderProposal(result, proposal, deviceResponse.devices || []);
      else renderFallback(result, proposal);
    } catch (error) {
      renderFallback(result, { scene_name: 'Manual scene required', trigger: { type: 'resident_arrives' }, conditions: [], actions: [], status: 'service_unavailable', explanation: 'Use the visual scene builder instead.', reason: error instanceof Error ? error.message : 'Backend unavailable' });
    } finally {
      submit.disabled = false;
      submit.textContent = 'Create';
    }
  };
  submit.addEventListener('click', () => void run(input.value));

  document.querySelectorAll<HTMLButtonElement>('.chip[data-nl]').forEach(oldChip => {
    const chip = oldChip.cloneNode(true) as HTMLButtonElement;
    oldChip.replaceWith(chip);
    chip.addEventListener('click', () => { input.value = chip.dataset.nl || ''; void run(input.value); });
  });
}

export default function App() {
  const host = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (!host.current) return;
    const style = document.createElement('style');
    style.dataset.livlinkPrototype = 'true';
    style.textContent = styleText;
    document.head.appendChild(style);
    const polish = document.createElement('style');
    polish.dataset.livlinkPolish = 'true';
    polish.textContent = polishStyles;
    document.head.appendChild(polish);
    const font = document.createElement('link');
    font.rel = 'stylesheet';
    font.href = 'https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,500&display=swap';
    document.head.appendChild(font);
    host.current.innerHTML = bodyMarkup;
    Function(`${prototypeScript}\nwindow.toast = toast; window.logActivity = logActivity;`)();
    wireBackendSceneComposer();
    return () => { style.remove(); polish.remove(); font.remove(); };
  }, []);
  return <div ref={host} />;
}
