import { useLayoutEffect, useRef } from 'react';
import prototypeDocument from '../../livlink-prototype.html?raw';
import polishStyles from './polish.css?inline';
import { confirmScene, parseScene, simulateArrival, getDevices, getScenes, deleteScene, getInsights, dismissInsight, applyInsight, getMqttStatus, getMaintenanceRequests, assignMaintenanceRequest, resolveMaintenanceRequest, type Device, type Proposal, type SavedScene, type AIInsight, type MaintenanceRequest } from './api';

const styleText = prototypeDocument.match(/<style>([\s\S]*?)<\/style>/i)?.[1] ?? '';
const bodyMarkup = prototypeDocument.match(/<body>([\s\S]*?)<script>/i)?.[1] ?? '';
const prototypeScript = prototypeDocument.match(/<script>([\s\S]*?)<\/script>/i)?.[1] ?? '';

declare global {
  interface Window {
    toast?: (message: string) => void;
    logActivity?: (message: string, category?: string) => void;
    renderSavedDbScenes?: () => void;
    openOperatorMaintenance?: () => void;
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
    <p id="backendSceneSaveStatus" class="fine" role="status" aria-live="polite" style="display:none;margin-top:10px;"></p>
  </div>`;
  document.querySelector('#backendEditScene')?.addEventListener('click', () => document.querySelector('#dndPalette')?.scrollIntoView({ behavior: 'smooth', block: 'center' }));
  document.querySelector('#backendConfirmScene')?.addEventListener('click', async event => {
    const button = event.currentTarget as HTMLButtonElement;
    button.disabled = true;
    button.textContent = 'Saving…';
    try {
      const saved = await confirmScene(proposal, currentRole());
      button.textContent = 'Saved ✓';
      window.toast?.(`${saved.name} confirmed and stored in PostgreSQL`);
      window.logActivity?.(`Scene confirmed — ${saved.name} (backend id ${saved.id})`, 'ok');
      window.dispatchEvent(new Event('livlink:saved-scene'));
      const status = document.querySelector<HTMLElement>('#backendSceneSaveStatus');
      if (status) {
        status.style.display = 'block';
        status.style.color = 'var(--success)';
        status.textContent = `✓ “${saved.name}” has been confirmed and saved (scene #${saved.id}).`;
      }
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
      const message = error instanceof Error ? error.message : 'Scene confirmation failed';
      const status = document.querySelector<HTMLElement>('#backendSceneSaveStatus');
      if (status) {
        status.style.display = 'block';
        status.style.color = 'var(--danger)';
        status.textContent = /already used|was not produced/i.test(message)
          ? 'This draft was already saved or expired. Create a fresh draft before saving again.'
          : message;
      }
      window.toast?.(message);
    }
  });
}

function savedSceneActionLabel(scene: SavedScene, devices: Device[]) {
  return scene.actions.map(action => {
    const suffix = action.value == null ? '' : action.action === 'set_temperature' ? ` → ${action.value}°C` : ` → ${action.value}%`;
    return `${deviceName(action.device_id, devices)} · ${action.action.replace(/_/g, ' ')}${suffix}`;
  });
}

function wireSavedScenesLibrary() {
  let disposed = false;

  const refresh = async () => {
    const host = document.querySelector<HTMLElement>('#sceneCards');
    if (!host) return;
    try {
      const [{ scenes }, { devices }] = await Promise.all([getScenes(), getDevices()]);
      if (disposed) return;
      host.querySelectorAll<HTMLElement>('[data-backend-scene]').forEach(card => card.remove());
      scenes.forEach(scene => {
        const actions = savedSceneActionLabel(scene, devices);
        host.insertAdjacentHTML('beforeend', `<article class="card backend-saved-scene" data-backend-scene="${scene.id}">
          <div class="row between" style="gap:10px;">
            <div class="scenehero"><div class="sic">✨</div><div><b style="font-size:16.5px;">${escapeHtml(scene.name)}</b><div class="fine">Confirmed scene · #${scene.id}</div></div></div>
            <span class="tag tag-build" data-scene-status><span class="dot"></span>Confirmed</span>
          </div>
          <div class="stack" style="gap:5px; margin:12px 0;">
            ${actions.map(action => `<div class="fine">• ${escapeHtml(action)}</div>`).join('')}
          </div>
          <div class="row" style="gap:8px; flex-wrap:wrap;">
            <button class="btn btn-primary btn-sm" data-scene-run>Run now</button>
            <button class="btn btn-ghost btn-sm" data-scene-edit>Edit</button>
            <button class="btn btn-ghost btn-sm" data-scene-pause>Pause</button>
            <button class="btn btn-danger btn-sm" data-scene-delete>Delete</button>
          </div>
        </article>`);
        const card = host.querySelector<HTMLElement>(`[data-backend-scene="${scene.id}"]`);
        const runButton = card?.querySelector<HTMLButtonElement>('[data-scene-run]');
        const pauseButton = card?.querySelector<HTMLButtonElement>('[data-scene-pause]');
        const status = card?.querySelector<HTMLElement>('[data-scene-status]');
        runButton?.addEventListener('click', () => {
          if (card?.dataset.paused === 'true') return;
          runButton.disabled = true;
          runButton.textContent = 'Requested…';
          window.setTimeout(() => {
            runButton.textContent = 'Acknowledged';
            window.toast?.(`${scene.name} — ${scene.actions.length} simulated device action${scene.actions.length === 1 ? '' : 's'} acknowledged`);
            window.logActivity?.(`${scene.name} scene ran — ${scene.actions.length} simulated device acknowledgement${scene.actions.length === 1 ? '' : 's'}`, 'ok');
            window.setTimeout(() => {
              runButton.textContent = 'Run now';
              runButton.disabled = card?.dataset.paused === 'true';
            }, 850);
          }, 550);
        });
        card?.querySelector<HTMLButtonElement>('[data-scene-edit]')?.addEventListener('click', () => {
          document.querySelector('#dndPalette')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          window.toast?.(`Edit “${scene.name}” in the visual builder`);
        });
        pauseButton?.addEventListener('click', () => {
          const paused = card?.dataset.paused !== 'true';
          if (!card || !status || !runButton) return;
          card.dataset.paused = String(paused);
          pauseButton.textContent = paused ? 'Resume' : 'Pause';
          runButton.disabled = paused;
          status.className = `tag ${paused ? 'tag-sim' : 'tag-build'}`;
          status.innerHTML = `<span class="dot"></span>${paused ? 'Paused' : 'Confirmed'}`;
          window.toast?.(`${scene.name} ${paused ? 'paused' : 'resumed'}`);
        });
        card?.querySelector<HTMLButtonElement>('[data-scene-delete]')?.addEventListener('click', async () => {
          if (!window.confirm(`Delete “${scene.name}”? This removes the saved scene.`)) return;
          const button = card.querySelector<HTMLButtonElement>('[data-scene-delete]');
          if (!button) return;
          button.disabled = true;
          button.textContent = 'Deleting…';
          try {
            await deleteScene(scene.id);
            card.remove();
            window.toast?.(`“${scene.name}” deleted`);
            window.logActivity?.(`Scene deleted — ${scene.name}`, 'warn');
          } catch (error) {
            button.disabled = false;
            button.textContent = 'Delete';
            window.toast?.(error instanceof Error ? error.message : 'Could not delete the scene');
          }
        });
      });
    } catch {
      // The fixed prototype scenes remain usable if the backend is unavailable.
    }
  };

  const onSaved = () => void refresh();
  window.renderSavedDbScenes = onSaved;
  window.addEventListener('livlink:saved-scene', onSaved);
  void refresh();
  return () => {
    disposed = true;
    window.removeEventListener('livlink:saved-scene', onSaved);
    delete window.renderSavedDbScenes;
  };
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


// ---------------------------------------------------------------------------
// AI Intelligence Panel — insight cards from /api/insights
// ---------------------------------------------------------------------------

const CATEGORY_CONFIG: Record<string, { icon: string; colorClass: string }> = {
  energy: { icon: '⚡', colorClass: 'insight-energy' },
  maintenance: { icon: '🔧', colorClass: 'insight-maintenance' },
  automation: { icon: '💡', colorClass: 'insight-automation' },
};

function renderInsightCard(insight: AIInsight): string {
  const config = CATEGORY_CONFIG[insight.category] || { icon: '📊', colorClass: '' };
  const body = insight.body as Record<string, unknown>;
  const severity = insight.severity;

  let detail = '';
  if (insight.category === 'energy') {
    detail = `
      <div class="insight-stats">
        <div class="insight-stat"><span class="insight-stat-label">Current</span><span class="insight-stat-value">${body.current_kwh} kWh</span></div>
        <div class="insight-stat"><span class="insight-stat-label">Typical</span><span class="insight-stat-value">${body.typical_kwh} kWh</span></div>
        <div class="insight-stat"><span class="insight-stat-label">Deviation</span><span class="insight-stat-value ${severity === 'critical' ? 'critical-text' : 'warning-text'}">+${body.deviation_pct}%</span></div>
      </div>
      <p class="fine" style="margin-top:8px;">${escapeHtml(String(body.recommendation || ''))}</p>`;
  } else if (insight.category === 'maintenance') {
    const factors = (body.factors as string[]) || [];
    const trend = (body.battery_trend as Record<string, unknown> | undefined) || {};
    const request = (body.maintenance_request as Record<string, unknown> | undefined) || {};
    const requestStatus = String(request.status || 'pending');
    const requestLabel = requestStatus === 'assigned'
      ? `Assigned to ${String(request.assigned_to || 'operator')}`
      : requestStatus === 'resolved'
        ? 'Resolved by Operator'
        : requestStatus === 'open'
          ? 'Request sent to Operator'
          : 'Preparing operator request';
    detail = `
      <div class="insight-stats">
        <div class="insight-stat"><span class="insight-stat-label">Battery</span><span class="insight-stat-value ${(body.battery_pct as number) < 20 ? 'critical-text' : ''}">${body.battery_pct}%</span></div>
        <div class="insight-stat"><span class="insight-stat-label">Failures</span><span class="insight-stat-value">${body.connection_failures} today</span></div>
        <div class="insight-stat"><span class="insight-stat-label">Risk</span><span class="insight-stat-value ${body.risk_level === 'high' ? 'critical-text' : 'warning-text'}">${String(body.risk_level).toUpperCase()}</span></div>
      </div>
      <div class="insight-factors">${factors.map(f => `<span class="insight-factor">${escapeHtml(f)}</span>`).join('')}</div>
      <p class="fine" style="margin-top:8px;">Decision: ${escapeHtml(String(trend.start_pct ?? '—'))}% → ${escapeHtml(String(trend.end_pct ?? body.battery_pct))}% over ${escapeHtml(String(trend.reading_count ?? '—'))} readings; ${escapeHtml(String(body.connection_failures ?? '—'))} connection failures.</p>
      <p class="fine" style="margin-top:8px;">${escapeHtml(String(body.recommendation || ''))}</p>
      <div class="maintenance-decision" style="margin-top:10px; padding:10px 12px; border-radius:12px; background:rgba(255,255,255,.58); border:1px solid rgba(190,70,85,.16);">
        <b style="font-size:13px;">${escapeHtml(requestLabel)}</b>
        <p class="fine" style="margin:3px 0 8px;">The automated action only opens a maintenance work item. The operator keeps control of assignment and resolution.</p>
        <button class="btn btn-secondary btn-sm" onclick="window.openOperatorMaintenance?.()">View operator request</button>
      </div>`;
  } else if (insight.category === 'automation') {
    const scene = body.suggested_scene as Record<string, unknown> | undefined;
    const actions = (scene?.actions as Array<Record<string, unknown>>) || [];
    detail = `
      <p style="font-size:15px; line-height:1.5; margin-bottom:10px;">${escapeHtml(String(body.description || ''))}</p>
      <div class="insight-scene-preview">
        <b>${escapeHtml(String(scene?.scene_name || 'Suggested Scene'))}</b>
        ${actions.map(a => {
          const valStr = a.value != null ? (a.action === 'set_temperature' ? ` → ${a.value}°C` : ` → ${a.value}%`) : '';
          return `<div class="fine">• ${escapeHtml(String(a.device_id))} · ${String(a.action).replace(/_/g, ' ')}${valStr}</div>`;
        }).join('')}
      </div>
      <p class="fine" style="margin-top:6px;">Pattern seen ${body.pattern_matches}/${body.pattern_days} days</p>`;
  }

  const buttons = insight.category === 'automation'
    ? `<button class="btn btn-primary btn-sm" data-apply="${insight.id}">Accept</button>
       <button class="btn btn-ghost btn-sm" data-dismiss="${insight.id}">Not now</button>`
    : insight.category === 'maintenance'
    ? `<button class="btn btn-ghost btn-sm" data-dismiss="${insight.id}">Dismiss resident alert</button>`
    : `<button class="btn btn-ghost btn-sm" data-dismiss="${insight.id}">Dismiss</button>`;

  return `<div class="insight-card ${config.colorClass} ${severity === 'critical' ? 'insight-pulse' : ''}" data-insight-id="${insight.id}">
    <div class="row between" style="margin-bottom:8px;">
      <div class="row" style="gap:8px; align-items:center;">
        <span style="font-size:20px;">${config.icon}</span>
        <b style="font-size:15.5px;">${escapeHtml(insight.title)}</b>
      </div>
      <span class="tag ${severity === 'critical' ? 'tag-critical' : severity === 'warning' ? 'tag-warning' : 'tag-sim'}">
        <span class="dot"></span>${escapeHtml(String(body.device_name || insight.category))}
      </span>
    </div>
    ${detail}
    <div class="row" style="gap:8px; margin-top:10px; flex-wrap:wrap;">${buttons}</div>
  </div>`;
}

function requestStatusText(request: MaintenanceRequest) {
  if (request.status === 'assigned') return `Assigned · ${request.assigned_to || 'Facilities technician'}`;
  if (request.status === 'resolved') return 'Resolved';
  return 'Open';
}

function wireMaintenanceRequests() {
  const queue = document.querySelector<HTMLElement>('#maintQueue');
  if (!queue) return;
  let disposed = false;

  const refresh = async () => {
    try {
      const { requests } = await getMaintenanceRequests();
      if (disposed) return;
      if (!requests.length) {
        queue.innerHTML = '<p class="fine" style="padding:10px 0;">No AI-routed maintenance requests yet.</p>';
        return;
      }
      queue.innerHTML = requests.map(request => {
        const decision = request.decision;
        const statusClass = request.status === 'resolved' ? 'tag-build' : request.status === 'assigned' ? 'tag-warning' : 'tag-critical';
        const controls = request.status === 'open'
          ? `<button class="btn btn-primary btn-sm" data-request-assign="${request.id}">Assign</button><button class="btn btn-ghost btn-sm" data-request-resolve="${request.id}">Resolve</button>`
          : request.status === 'assigned'
            ? `<button class="btn btn-primary btn-sm" data-request-resolve="${request.id}">Resolve</button>`
            : '';
        return `<article class="maintenance-request-card" data-request-id="${request.id}">
          <div class="row between" style="gap:10px; flex-wrap:wrap;">
            <div><b style="font-size:15px;">Unit ${escapeHtml(request.unit)} — ${escapeHtml(request.title)}</b><p class="fine" style="margin-top:4px;">AI decision: ${decision.battery_pct}% battery · ${decision.trend_start_pct}% → ${decision.trend_end_pct}% across ${decision.reading_count} readings · ${decision.connection_failures} connection failures.</p></div>
            <div class="row" style="gap:6px;"><span class="tag ${statusClass}"><span class="dot"></span>${escapeHtml(requestStatusText(request))}</span><span class="tag tag-sim"><span class="dot"></span>AI-routed</span></div>
          </div>
          <p class="fine" style="margin-top:8px;">${escapeHtml(decision.reason)} Device telemetry is simulated for this demo.</p>
          ${controls ? `<div class="row" style="gap:8px; margin-top:10px; flex-wrap:wrap;">${controls}</div>` : ''}
        </article>`;
      }).join('');

      queue.querySelectorAll<HTMLButtonElement>('[data-request-assign]').forEach(button => {
        button.addEventListener('click', async () => {
          const id = Number(button.dataset.requestAssign);
          button.disabled = true;
          button.textContent = 'Assigning…';
          try {
            await assignMaintenanceRequest(id);
            window.toast?.('Maintenance request assigned to Facilities technician');
            window.logActivity?.('Operator assigned AI maintenance request', 'ok');
            await refresh();
          } catch (error) {
            button.disabled = false;
            button.textContent = 'Assign';
            window.toast?.(error instanceof Error ? error.message : 'Could not assign request');
          }
        });
      });
      queue.querySelectorAll<HTMLButtonElement>('[data-request-resolve]').forEach(button => {
        button.addEventListener('click', async () => {
          const id = Number(button.dataset.requestResolve);
          button.disabled = true;
          button.textContent = 'Resolving…';
          try {
            await resolveMaintenanceRequest(id);
            window.toast?.('Maintenance request resolved; resident status updated');
            window.logActivity?.('Operator resolved AI maintenance request', 'ok');
            await refresh();
          } catch (error) {
            button.disabled = false;
            button.textContent = 'Resolve';
            window.toast?.(error instanceof Error ? error.message : 'Could not resolve request');
          }
        });
      });
    } catch {
      queue.innerHTML = '<p class="fine" style="padding:10px 0;">Could not load the operator queue.</p>';
    }
  };

  void refresh();
  const timer = setInterval(() => void refresh(), 5000);
  return () => { disposed = true; clearInterval(timer); };
}

function wireInsightPanel() {
  const container = document.querySelector<HTMLElement>('#insightCards');
  const mqttDot = document.querySelector<HTMLElement>('#mqttDot');
  if (!container) return;
  const cards = container;

  let pollTimer: ReturnType<typeof setInterval> | null = null;

  async function refresh() {
    try {
      const [{ insights }, mqttStatus] = await Promise.all([getInsights(), getMqttStatus().catch(() => ({ connected: false, events_received: 0 }))]);

      // Update the simulated event-stream status dot.
      if (mqttDot) {
        mqttDot.classList.toggle('connected', mqttStatus.connected);
        mqttDot.title = mqttStatus.connected
          ? `Simulated event stream connected · ${mqttStatus.events_received} events`
          : 'Simulated event stream disconnected';
      }

      if (!insights.length) {
        cards.innerHTML = '<div class="insight-placeholder fine" style="padding:18px; text-align:center; color:var(--text-3);">No active insights — all systems normal ✓</div>';
        return;
      }

      cards.innerHTML = insights.map(renderInsightCard).join('');

      // Wire dismiss buttons
      cards.querySelectorAll<HTMLButtonElement>('[data-dismiss]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = Number(btn.dataset.dismiss);
          btn.disabled = true;
          btn.textContent = 'Dismissing…';
          try {
            await dismissInsight(id);
            const card = btn.closest<HTMLElement>('.insight-card');
            if (card) { card.style.opacity = '0'; card.style.transform = 'translateX(20px)'; setTimeout(() => card.remove(), 300); }
            window.toast?.('Insight dismissed');
            window.logActivity?.('AI insight dismissed', 'ok');
          } catch { btn.disabled = false; btn.textContent = 'Dismiss'; }
        });
      });

      // Wire apply buttons
      cards.querySelectorAll<HTMLButtonElement>('[data-apply]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = Number(btn.dataset.apply);
          btn.disabled = true;
          btn.textContent = 'Creating scene…';
          try {
            const result = await applyInsight(id);
            btn.textContent = 'Scene created ✓';
            window.toast?.(`${result.name} saved as a new scene`);
            window.logActivity?.(`AI automation applied — ${result.name} (id ${result.id})`, 'ok');
          } catch { btn.disabled = false; btn.textContent = 'Accept'; }
        });
      });
    } catch {
      cards.innerHTML = '<div class="insight-placeholder fine" style="padding:18px; text-align:center; color:var(--text-3);">Could not load insights — is the backend running?</div>';
    }
  }

  // Initial load + poll every 5 seconds
  void refresh();
  pollTimer = setInterval(() => void refresh(), 5000);

  // Cleanup on unmount (not strictly needed for prototype but good practice)
  return () => { if (pollTimer) clearInterval(pollTimer); };
}


export default function App({ initialRole }: { initialRole?: string } = {}) {
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
    const cleanupSavedScenes = wireSavedScenesLibrary();
    const cleanupInsights = wireInsightPanel();
    const cleanupMaintenance = wireMaintenanceRequests();
    if (initialRole && initialRole !== 'owner') {
      document.querySelector<HTMLButtonElement>(`#rolePill button[data-role="${initialRole}"]`)?.click();
    }
    return () => { style.remove(); polish.remove(); font.remove(); cleanupSavedScenes?.(); cleanupInsights?.(); cleanupMaintenance?.(); };
  }, []);
  return <div ref={host} />;
}
