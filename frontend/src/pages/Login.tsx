import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Train, Loader2, ShieldCheck, User as UserIcon, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '../utils/helpers';

function RailwayNetworkVisual() {
  const nodes = [
    { top: '18%', left: '12%' },
    { top: '12%', left: '38%' },
    { top: '30%', left: '58%' },
    { top: '22%', left: '82%' },
    { top: '52%', left: '18%' },
    { top: '48%', left: '44%' },
    { top: '62%', left: '66%' },
    { top: '56%', left: '88%' },
    { top: '78%', left: '30%' },
    { top: '74%', left: '56%' },
    { top: '84%', left: '80%' },
  ];
  return (
    <div className="relative h-full w-full overflow-hidden">
      <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-60" />
      <div className="absolute inset-0 bg-radial-glow" />

      {nodes.map((n, i) => (
        <div key={i}>
          <span
            className="absolute w-1.5 h-1.5 rounded-full bg-accent/70"
            style={{ top: n.top, left: n.left, boxShadow: '0 0 8px rgba(0,212,255,0.6)' }}
          />
        </div>
      ))}

      {nodes.slice(0, nodes.length - 1).map((n, i) => (
        <svg key={`l${i}`} className="absolute inset-0 h-full w-full pointer-events-none">
          <line
            x1={`${n.left}`}
            y1={`${n.top}`}
            x2={`${nodes[i + 1].left}`}
            y2={`${nodes[i + 1].top}`}
            stroke="rgba(0,212,255,0.15)"
            strokeWidth="1"
            strokeDasharray="4 6"
          />
        </svg>
      ))}

      <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-violet-500 flex items-center justify-center shadow-glow-lg mb-5">
          <Train className="h-8 w-8 text-surface-50" strokeWidth={2.5} />
        </div>
        <p className="text-sm font-semibold text-accent tracking-[0.3em] uppercase">Real-Time Railway Intelligence</p>

        <div className="mt-8 flex items-center gap-2 text-[11px] font-mono text-gray-500">
          <span className="w-2 h-2 rounded-full bg-rail-green animate-pulse-slow" />
          <span>LIVE FEED SIMULATED</span>
          <span className="mx-2 text-gray-700">•</span>
          <span>AI ETA ENGINE</span>
          <span className="mx-2 text-gray-700">•</span>
          <span>OPERATIONS READY</span>
        </div>
      </div>
    </div>
  );
}

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await login(username, password);
      toast.success('Welcome back');
      navigate('/');
    } catch {
      setError('Invalid username or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-50 flex">
      <div className="hidden lg:block w-[46%] relative border-r border-white/[0.06]">
        <RailwayNetworkVisual />
        <div className="absolute bottom-8 left-0 right-0 text-center">
          <p className="text-[11px] tracking-[0.2em] uppercase text-gray-600">Smart India Hackathon · RailPulse AI</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md animate-slide-up">
          <div className="lg:hidden flex justify-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent to-violet-500 flex items-center justify-center shadow-glow">
              <Train className="h-7 w-7 text-surface-50" strokeWidth={2.5} />
            </div>
          </div>

          <div className="flex items-center gap-3 mb-8">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-[11px] font-semibold text-gray-400">
              <ShieldCheck className="h-3.5 w-3.5 text-rail-green" /> Railway Operations Portal
            </span>
          </div>

          <h1 className="text-display-md font-bold text-gray-50">
            Predict every arrival.
            <br />
            <span className="text-accent">Understand every delay.</span>
          </h1>
          <p className="text-gray-500 mt-3 mb-8">
            Sign in to the RAILPULSE AI platform to track trains, predict ETAs and monitor operations in real time.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input pl-9"
                  placeholder="Enter username"
                  required
                  autoComplete="username"
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Enter password"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-lg bg-rail-red/10 border border-rail-red/20 px-4 py-3 text-sm text-rail-red animate-fade-in" role="alert">
                {error}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="btn-primary w-full py-2.5 mt-2">
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" /> Signing in…
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className={cn('mt-6 rounded-lg border border-dashed border-white/10 px-4 py-3 text-xs text-gray-500 space-y-0.5')}>
            <p className="font-medium text-gray-400">Demo environment — sample credentials</p>
            <p className="font-mono text-gray-500"><span className="text-gray-300">passenger</span> / <span className="text-gray-300">passenger123</span> · <span className="text-gray-300">operator</span> / <span className="text-gray-300">operator123</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}