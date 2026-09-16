import { useState, type FormEvent } from 'react';
import './LoginGate.css';
import loginHero from './assets/livlink-smart-home-login-hero.png';
import logoMark from './assets/livlink-logo-mark.png';

type Role = 'owner' | 'occupier' | 'tenant';

const ROLES: { id: Role; label: string; icon: string; blurb: string }[] = [
  { id: 'owner', label: 'Owner', icon: '🏠', blurb: 'Full control — billing, property transfer and every device.' },
  { id: 'occupier', label: 'Occupier', icon: '🛋️', blurb: 'Everyday living — scenes, visitors and devices stay open.' },
  { id: 'tenant', label: 'Tenant', icon: '🔑', blurb: 'Device control and visitors stay open; billing stays locked.' },
];

export default function LoginGate({ onEnter }: { onEnter: (role: Role) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onEnter('owner');
  };

  return (
    <div className="lg-page">
      <span className="lg-mark lg-mark-1">✕</span>
      <span className="lg-mark lg-mark-2">✕</span>
      <span className="lg-mark lg-mark-3">✕</span>
      <span className="lg-mark lg-mark-4">✕</span>
      <span className="lg-mark lg-mark-5">✕</span>

      <div className="lg-shell">
        <div className="lg-brand-panel">
          <div className="lg-logo">
            <img className="lg-logo-mark" src={logoMark} alt="" />
            <span className="lg-logo-word">LIVLINK</span>
          </div>
          <div className="lg-hero-art">
            <img src={loginHero} alt="A resident arriving home to a responsive smart apartment at twilight." />
          </div>
          <h1 className="lg-headline">Your home,<br />understood.</h1>
          <p className="lg-sub">One platform for owners, occupiers and tenants to see, schedule and hand off a smart home — safely.</p>
          <div className="lg-brand-foot">Natural-language scenes · Real-time insights · Role-aware access</div>
        </div>

        <div className="lg-form-panel">
          <div className="lg-tabs" role="tablist">
            <button type="button" role="tab" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Log In</button>
            <button type="button" role="tab" className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Sign Up</button>
          </div>

          <form className="lg-form" onSubmit={handleSubmit}>
            <h2 className="lg-form-title">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
            {mode === 'signup' && (
              <label className="lg-field">
                <span>Full name</span>
                <input type="text" placeholder="Jane Perera" autoComplete="name" />
              </label>
            )}
            <label className="lg-field">
              <span>Email</span>
              <input type="email" placeholder="you@livlink.com" autoComplete="email" />
            </label>
            <label className="lg-field">
              <span>Password</span>
              <input type="password" placeholder="••••••••" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
            </label>
            <button type="submit" className="lg-submit">{mode === 'login' ? 'Log In' : 'Create account'}</button>
            <p className="lg-note">Demo build — no account is created. Pick a role below to jump straight into LIVLINK.</p>
          </form>

          <div className="lg-divider"><span>or preview as</span></div>

          <div className="lg-roles">
            {ROLES.map(role => (
              <button key={role.id} type="button" className="lg-role-card" onClick={() => onEnter(role.id)}>
                <span className="lg-role-icon">{role.icon}</span>
                <span className="lg-role-copy">
                  <b>{role.label}</b>
                  <span>{role.blurb}</span>
                </span>
                <span className="lg-role-arrow">→</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
