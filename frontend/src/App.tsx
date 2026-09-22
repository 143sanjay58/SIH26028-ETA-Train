import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { AppShell } from './components/layout/AppShell';
import { Loader2 } from 'lucide-react';
import Login from './pages/Login';
import PassengerDashboard from './pages/PassengerDashboard';
import TrainDetail from './pages/TrainDetail';
import LiveTrains from './pages/LiveTrains';
import RailwayMapPage from './pages/RailwayMapPage';
import ETAEngine from './pages/ETAEngine';
import DelayIntelligence from './pages/DelayIntelligence';
import WeatherIntelligence from './pages/WeatherIntelligence';
import AlertCenter from './pages/AlertCenter';
import Analytics from './pages/Analytics';
import SimulationLab from './pages/SimulationLab';
import StationMaster from './pages/StationMaster';
import ControlRoom from './pages/ControlRoom';
import CoPilot from './pages/CoPilot';
import SystemHealth from './pages/SystemHealth';
import Settings from './pages/Settings';

function FullScreenLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 text-accent animate-spin" />
        <span className="text-sm text-gray-500">Connecting to RAILPULSE AI…</span>
      </div>
    </div>
  );
}

function PrivateRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <FullScreenLoader />;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function App() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <FullScreenLoader />;

  const rest =
    user?.role === 'STATION_STAFF' ? <Navigate to="/co-pilot" replace /> :
    user && ['SUPERVISOR', 'OPERATOR', 'ADMIN'].includes(user.role) ? <Navigate to="/control-room" replace /> :
    user ? <Navigate to="/" replace /> : null;

  return (
    <Routes>
      <Route path="/login" element={user ? (rest ? rest : <Navigate to="/" replace />) : <Login />} />

      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppShell />
          </PrivateRoute>
        }
      >
        <Route index element={<PassengerDashboard />} />
        <Route path="train/:trainNumber" element={<TrainDetail />} />
        <Route path="trains" element={<LiveTrains />} />
        <Route path="map" element={<RailwayMapPage />} />
        <Route path="eta" element={<ETAEngine />} />
        <Route path="delay-intel" element={<DelayIntelligence />} />
        <Route path="weather" element={<WeatherIntelligence />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="simulation" element={<SimulationLab />} />
        <Route path="alerts" element={<AlertCenter />} />
        <Route path="system-health" element={<SystemHealth />} />
        <Route path="settings" element={<Settings />} />

        <Route
          path="control-room"
          element={
            <PrivateRoute allowedRoles={['SUPERVISOR', 'OPERATOR', 'ADMIN']}>
              <ControlRoom />
            </PrivateRoute>
          }
        />
        <Route
          path="station-master"
          element={
            <PrivateRoute allowedRoles={['STATION_STAFF', 'SUPERVISOR', 'OPERATOR', 'ADMIN']}>
              <StationMaster />
            </PrivateRoute>
          }
        />
        <Route
          path="co-pilot"
          element={
            <PrivateRoute allowedRoles={['STATION_STAFF']}>
              <CoPilot />
            </PrivateRoute>
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;