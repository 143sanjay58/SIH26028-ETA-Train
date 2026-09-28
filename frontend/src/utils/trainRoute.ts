import { trainApi, sihEtaApi, stationApi } from '../services/api';

export interface RouteStationInfo {
  code: string;
  name: string;
  position: number;
  station_id?: number;
}

export async function loadTrainRoute(trainNumber: string, trainId?: number): Promise<RouteStationInfo[]> {
  const byCode = new Map<string, RouteStationInfo>();
  const push = (code: string | undefined, name: string | undefined, position: number, stationId?: number) => {
    if (!code) return;
    if (!byCode.has(code)) {
      byCode.set(code, { code, name: name || code, position, station_id: stationId });
    }
  };

  if (trainId != null) {
    const routeRes = await trainApi.getRoute(trainId).catch(() => null);
    if (routeRes?.data) {
      const rd = routeRes.data;
      if (rd.origin) push(rd.origin.station_code, rd.origin.station_name, rd.origin.sequence, rd.origin.station_id);
      (rd.passed_stations || []).forEach((s) => push(s.station_code, s.station_name, s.sequence, s.station_id));
      (rd.upcoming_stations || []).forEach((s) => push(s.station_code, s.station_name, s.sequence, s.station_id));
      if (rd.destination) push(rd.destination.station_code, rd.destination.station_name, rd.destination.sequence, rd.destination.station_id);
    }
  }

  if (byCode.size === 0) {
    const etaRes = await sihEtaApi.getETA(trainNumber).catch(() => null);
    if (etaRes?.data) {
      const eta = etaRes.data;
      push(eta.current_station, eta.current_station_name, eta.current_route_position || 0);
      (eta.upcoming_stations || []).forEach((u) => push(u.station_code, u.station_name, u.route_position || 0));
      push(eta.destination_station, eta.destination_station_name, (eta.current_route_position || 0) + (eta.upcoming_station_count || 0) + 1);
    }
  }

  const ordered = [...byCode.values()].sort((a, b) => a.position - b.position);

  const unresolved = ordered.filter((s) => s.station_id === undefined).map((s) => s.code);
  if (unresolved.length) {
    const results = await Promise.allSettled(unresolved.map((c) => stationApi.getByCode(c)));
    unresolved.forEach((code, i) => {
      const r = results[i];
      if (r.status === 'fulfilled') {
        const match = ordered.find((s) => s.code === code);
        if (match) match.station_id = r.value.data.id;
      }
    });
  }

  return ordered;
}