import { useState, useEffect } from 'react';
import { stationApi, trainApi, alertApi } from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';
import {
  Plus,
  Edit,
  Building2,
  AlertTriangle,
  ShieldCheck,
  Loader2,
} from 'lucide-react';
import { cn, formatDateTime, getSeverityBg, getEventTypeLabel } from '../utils/helpers';
import { SectionHeader } from '../components/ui/SectionHeader';
import { MetricCard } from '../components/ui/MetricCard';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/EmptyState';
import { useAuth } from '../contexts/AuthContext';
import type { StationReport, StationReportStatus, StationReportEventType, Train, Alert } from '../types';
import toast from 'react-hot-toast';

const EVENT_TYPES: { value: StationReportEventType; label: string }[] = [
  { value: 'SIGNAL_WAIT', label: 'Signal Wait' },
  { value: 'PLATFORM_OCCUPIED', label: 'Platform Occupied' },
  { value: 'PRECEDING_TRAIN', label: 'Preceding Train' },
  { value: 'CROSSING_TRAIN', label: 'Crossing Train' },
  { value: 'CREW_CHANGE', label: 'Crew Change' },
  { value: 'TECHNICAL_CHECK', label: 'Technical Check' },
  { value: 'PASSENGER_ASSISTANCE', label: 'Passenger Assistance' },
  { value: 'MEDICAL_EMERGENCY', label: 'Medical Emergency' },
  { value: 'TRACK_WORK', label: 'Track Work' },
  { value: 'MAINTENANCE_BLOCK', label: 'Maintenance Block' },
  { value: 'LOCOMOTIVE_ISSUE', label: 'Locomotive Issue' },
  { value: 'COACH_ISSUE', label: 'Coach Issue' },
  { value: 'WATER_CLEANING', label: 'Water/Cleaning' },
  { value: 'WEATHER', label: 'Weather' },
  { value: 'SECURITY_CHECK', label: 'Security Check' },
  { value: 'OPERATIONAL_HOLD', label: 'Operational Hold' },
  { value: 'OTHER', label: 'Other' },
];

const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;

const STATUS_FLOW: Record<StationReportStatus, StationReportStatus[]> = {
  PENDING: ['VERIFIED', 'CANCELLED'],
  VERIFIED: ['PUBLISHED', 'CANCELLED'],
  PUBLISHED: ['RESOLVED', 'CANCELLED'],
  RESOLVED: [],
  CANCELLED: [],
};

const emptyForm = {
  train_id: '',
  event_type: 'SIGNAL_WAIT' as StationReportEventType,
  severity: 'MEDIUM' as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
  description: '',
  start_time: new Date().toISOString().slice(0, 16),
  expected_resolution: '',
  delay_impact_minutes: '',
};

export default function StationMaster() {
  const { user } = useAuth();
  const { onTrainUpdate, onAlert } = useWebSocket();
  const [reports, setReports] = useState<StationReport[]>([]);
  const [trains, setTrains] = useState<Train[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingReport, setEditingReport] = useState<StationReport | null>(null);
  const [selectedStationId, setSelectedStationId] = useState<number | null>(user?.station_id || null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [formData, setFormData] = useState(emptyForm);

  useEffect(() => {
    if (!selectedStationId) {
      setReports([]);
      setIsLoading(false);
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [reportsRes, trainsRes, alertsRes] = await Promise.all([
          stationApi.getReports(selectedStationId, { page: 1, page_size: 50 }),
          trainApi.list({ page_size: 100 }),
          alertApi.list({ station_id: selectedStationId, active_only: true }),
        ]);
        setReports(reportsRes.data.items);
        setTrains(trainsRes.data.trains || []);
        setAlerts(alertsRes.data);
      } catch { /* ignore */ } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const unsubTrain = onTrainUpdate(() => fetchData());
    const unsubAlert = onAlert(() => fetchData());
    return () => { unsubTrain(); unsubAlert(); };
  }, [selectedStationId, onTrainUpdate, onAlert]);

  const filteredReports = reports.filter((r) => filterStatus === 'all' || r.status === filterStatus);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStationId) return;
    try {
      if (editingReport) {
        await stationApi.updateReport(editingReport.id, {
          event_type: formData.event_type,
          severity: formData.severity,
          description: formData.description,
          expected_resolution: formData.expected_resolution || undefined,
          delay_impact_minutes: formData.delay_impact_minutes ? parseInt(formData.delay_impact_minutes) : undefined,
        });
        toast.success('Report updated');
      } else {
        await stationApi.createReport(selectedStationId, {
          train_id: parseInt(formData.train_id),
          event_type: formData.event_type,
          severity: formData.severity,
          description: formData.description,
          start_time: new Date(formData.start_time).toISOString(),
          expected_resolution: formData.expected_resolution ? new Date(formData.expected_resolution).toISOString() : undefined,
          delay_impact_minutes: formData.delay_impact_minutes ? parseInt(formData.delay_impact_minutes) : undefined,
        });
        toast.success('Report created');
      }
      setShowCreateModal(false);
      setEditingReport(null);
      setFormData(emptyForm);
    } catch {
      toast.error('Failed to save report');
    }
  };

  const handleEdit = (report: StationReport) => {
    setEditingReport(report);
    setFormData({
      train_id: report.train_id.toString(),
      event_type: report.event_type,
      severity: report.severity,
      description: report.description,
      start_time: report.start_time.slice(0, 16),
      expected_resolution: report.expected_resolution?.slice(0, 16) || '',
      delay_impact_minutes: report.delay_impact_minutes?.toString() || '',
    });
    setShowCreateModal(true);
  };

  const changeStatus = async (report: StationReport, newStatus: StationReportStatus) => {
    try {
      await stationApi.updateReport(report.id, { status: newStatus });
      toast.success(`Report ${newStatus.toLowerCase()}`);
      setReports((prev) => prev.map((r) => (r.id === report.id ? { ...r, status: newStatus } : r)));
    } catch {
      toast.error('Failed to update status');
    }
  };

  const pending = reports.filter((r) => r.status === 'PENDING').length;
  const verified = reports.filter((r) => r.status === 'VERIFIED' || r.status === 'PUBLISHED').length;
  const resolved = reports.filter((r) => r.status === 'RESOLVED').length;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Station Operations"
        subtitle="Operational event reporting & extended halt management"
        right={
          <button onClick={() => { setEditingReport(null); setFormData(emptyForm); setShowCreateModal(true); }} className="btn-primary btn-sm">
            <Plus className="h-4 w-4" /> New Report
          </button>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard icon={Building2} label="Active trains" value={trains.length} accent="cyan" />
        <MetricCard icon={AlertTriangle} label="Pending reports" value={pending} accent="amber" />
        <MetricCard icon={ShieldCheck} label="Verified reports" value={verified} accent="green" />
        <MetricCard icon={ShieldCheck} label="Resolved reports" value={resolved} accent="violet" />
      </div>

      <div className="card">
        <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b border-white/[0.06]">
          <label className="text-sm text-gray-500">Station:</label>
          <select
            value={selectedStationId || ''}
            onChange={(e) => setSelectedStationId(e.target.value ? parseInt(e.target.value) : null)}
            className="input h-8 w-auto text-sm"
          >
            <option value="">All stations</option>
            {user?.station_id && <option value={user.station_id}>My Station (ID: {user.station_id})</option>}
          </select>
          <label className="text-sm text-gray-500 ml-2">Status:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="input h-8 w-auto text-sm">
            <option value="all">All statuses</option>
            {Object.keys(STATUS_FLOW).map((k) => <option key={k} value={k}>{k.charAt(0) + k.slice(1).toLowerCase()}</option>)}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-white/[0.06]">
                <th className="table-header px-4 py-2.5">Train</th>
                <th className="table-header px-4 py-2.5">Event type</th>
                <th className="table-header px-4 py-2.5">Severity</th>
                <th className="table-header px-4 py-2.5">Description</th>
                <th className="table-header px-4 py-2.5">Start</th>
                <th className="table-header px-4 py-2.5">Impact</th>
                <th className="table-header px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={8} className="py-8 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto text-accent" /></td></tr>
              ) : filteredReports.length === 0 ? (
                <tr><td colSpan={8}><EmptyState title="No operational reports" message={selectedStationId ? 'No reports for this station yet.' : 'Select a station to view reports.'} /></td></tr>
              ) : filteredReports.map((report) => (
                <tr key={report.id} className="table-row">
                  <td className="px-4 py-3 font-mono font-medium text-gray-100">#{report.train_id}</td>
                  <td className="px-4 py-3">
                    <span className="badge-info">{getEventTypeLabel(report.event_type)}</span>
                  </td>
                  <td className="px-4 py-3"><span className={cn(getSeverityBg(report.severity))}>{report.severity}</span></td>
                  <td className="px-4 py-3 text-gray-400 max-w-xs truncate">{report.description}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{formatDateTime(report.start_time)}</td>
                  <td className="px-4 py-3 font-mono text-gray-300">{report.delay_impact_minutes ? `${report.delay_impact_minutes}m` : '—'}</td>
                  <td className="px-4 py-3"><span className={cn(getSeverityBg(report.status === 'PENDING' ? 'WARNING' : report.status === 'VERIFIED' || report.status === 'PUBLISHED' ? 'LOW' : 'NORMAL'))}>{report.status}</span></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <button onClick={() => handleEdit(report)} className="p-1.5 rounded-md text-gray-500 hover:text-gray-200 hover:bg-white/[0.06]" title="Edit">
                        <Edit className="h-3.5 w-3.5" />
                      </button>
                      <select
                        value={report.status}
                        onChange={(e) => changeStatus(report, e.target.value as StationReportStatus)}
                        className="input h-7 w-auto text-[11px] px-2"
                        aria-label={`Change status for report ${report.id}`}
                      >
                        {STATUS_FLOW[report.status].map((s) => <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>)}
                      </select>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-gray-200 mb-3">Active alerts at this station</h2>
          <div className="space-y-2">
            {alerts.slice(0, 5).map((a) => (
              <div key={a.id} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white/[0.03]">
                <span className={cn('w-1.5 h-1.5 rounded-full mt-1.5 shrink-0', a.severity === 'CRITICAL' ? 'bg-rail-red' : 'bg-rail-amber')} />
                <div className="flex-1">
                  <p className="text-sm text-gray-300">{a.title}</p>
                  <p className="text-xs text-gray-600">{a.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showCreateModal && (
        <Modal title={editingReport ? 'Edit Station Report' : 'Create Station Report'} onClose={() => { setShowCreateModal(false); setEditingReport(null); }}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Train</label>
              <select value={formData.train_id} onChange={(e) => setFormData({ ...formData, train_id: e.target.value })} className="input" required>
                <option value="">Select train</option>
                {trains.map((t) => <option key={t.id} value={t.id}>{t.train_number} — {t.train_name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Event type</label>
                <select value={formData.event_type} onChange={(e) => setFormData({ ...formData, event_type: e.target.value as StationReportEventType })} className="input" required>
                  {EVENT_TYPES.map((e) => <option key={e.value} value={e.value}>{e.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Severity</label>
                <select value={formData.severity} onChange={(e) => setFormData({ ...formData, severity: e.target.value as typeof formData.severity })} className="input" required>
                  {SEVERITIES.map((s) => <option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Description</label>
              <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="input min-h-[90px]" required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Start time</label>
                <input type="datetime-local" value={formData.start_time} onChange={(e) => setFormData({ ...formData, start_time: e.target.value })} className="input" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Expected resolution</label>
                <input type="datetime-local" value={formData.expected_resolution} onChange={(e) => setFormData({ ...formData, expected_resolution: e.target.value })} className="input" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Delay impact (minutes)</label>
              <input type="number" min="0" value={formData.delay_impact_minutes} onChange={(e) => setFormData({ ...formData, delay_impact_minutes: e.target.value })} className="input" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => { setShowCreateModal(false); setEditingReport(null); }} className="btn-secondary">Cancel</button>
              <button type="submit" className="btn-primary">{editingReport ? 'Update Report' : 'Create Report'}</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}