const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export type Action = { device_id: string; action: 'set_temperature' | 'set_level' | 'turn_on' | 'turn_off' | 'lock' | 'unlock'; value?: number | null };
export type Proposal = { proposal_id?: string; scene_name: string; trigger: { type: 'resident_arrives' }; conditions: { type: 'time_after'; value: string }[]; actions: Action[]; status: 'ready' | 'needs_clarification' | 'unsupported' | 'service_unavailable' | 'rejected'; explanation: string; reason?: string };
export type Device = { id: string; name: string; kind: string; room: string; state: Record<string, unknown> };
export type SavedScene = { id: number; name: string; role: string; trigger: { type: string }; conditions: { type: string; value: string }[]; actions: Action[] };
export type CommandResult = { device_id: string; action: string; transitions: ('requested' | 'acknowledged' | 'failed')[]; status: string; detail: string };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `Request failed (${response.status})`);
  return response.json() as Promise<T>;
}
export const getDevices = () => request<{ devices: Device[] }>('/devices');
export const getActivity = () => request<{ events: { id: number; message: string; category: string; created_at: string | null }[] }>('/activity');
export const getScenes = () => request<{ scenes: SavedScene[] }>('/scenes');
export const parseScene = (requestText: string, role: string) => request<Proposal>('/ai/scenes/parse', { method: 'POST', body: JSON.stringify({ request: requestText, role }) });
export const confirmScene = (proposal: Proposal, role: string) => request<{ id: number; name: string }>('/scenes/confirm', { method: 'POST', body: JSON.stringify({ proposal, role }) });
export const simulateArrival = () => request<{ executions: { scene_name: string; results: CommandResult[] }[] }>('/simulation/resident-arrival', { method: 'POST', body: JSON.stringify({}) });
