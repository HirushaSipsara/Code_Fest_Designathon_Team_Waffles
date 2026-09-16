import { useState } from 'react';
import App from './App';
import LoginGate from './LoginGate';

export default function Root() {
  const [role, setRole] = useState<string | null>(null);
  if (!role) return <LoginGate onEnter={setRole} />;
  return <App initialRole={role} />;
}
