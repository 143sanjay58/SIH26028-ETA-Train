export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  station_id?: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export type UserRole = 'PASSENGER' | 'STATION_STAFF' | 'SUPERVISOR' | 'OPERATOR' | 'ADMIN';

export interface Train {
  id: number;
  train_number: string;
  train_name: string;
  train_type: TrainType;
  origin_station_id: number;
  destination_station_id: number;
  route_id: number;
  total_stops: number;
  total_distance_km: number;
  scheduled_departure: string;
  scheduled_arrival: string;
  status: TrainStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  origin_station?: Station;
  destination_station?: Station;
}

export type TrainType = 'EXPRESS' | 'SUPERFAST' | 'MAIL' | 'PASSENGER' | 'SUBURBAN' | 'FREIGHT' | 'RAJDHANI' | 'SHATABDI' | 'DURONTO' | 'VANDE_BHARAT';

export type TrainStatus = 'SCHEDULED' | 'RUNNING' | 'DELAYED' | 'ARRIVED' | 'CANCELLED' | 'DIVERTED' | 'TERMINATED';

export interface Station {
  id: number;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  station_type: StationType;
  zone?: string;
  division?: string;
  state?: string;
  platform_count: number;
  is_junction: boolean;
  is_active: boolean;
}

export type StationType = 'JUNCTION' | 'TERMINAL' | 'HALT' | 'CROSSING' | 'BLOCK';

export interface TrainPosition {
  id: number;
  train_id: number;
  latitude: number;
  longitude: number;
  speed_kmh: number;
  heading?: number;
  current_station_id?: number;
  next_station_id?: number;
  distance_to_next_km?: number;
  distance_travelled_km: number;
  delay_minutes: number;
  timestamp: string;
  source: DataSource;
  is_valid: boolean;
}

export interface TrainSchedule {
  id: number;
  station_id: number;
  station_code: string;
  station_name: string;
  sequence: number;
  scheduled_arrival?: string;
  scheduled_departure?: string;
  scheduled_dwell_minutes: number;
  distance_from_origin_km: number;
  is_origin: boolean;
  is_destination: boolean;
  platform?: string;
}

export interface TrainLiveResponse {
  train: Train;
  current_position?: TrainPosition;
  next_station?: TrainSchedule;
  current_speed_kmh: number;
  average_speed_kmh: number;
  distance_travelled_km: number;
  distance_remaining_km: number;
  current_delay_minutes: number;
  delay_trend: string;
  eta_at_destination?: string;
  prediction_interval_lower?: string;
  prediction_interval_upper?: string;
  confidence_score?: number;
  data_source: DataSource;
}

export interface ETAResponse {
  train_number: string;
  train_name: string;
  current_station?: string;
  next_station?: string;
  destination_station: string;
  current_delay_minutes: number;
  predicted_arrival_delay_minutes: number;
  predicted_arrival_time: string;
  prediction_interval_lower?: string;
  prediction_interval_upper?: string;
  confidence_score?: number;
  model_type: string;
  model_version: string;
  explanations: Explanation[];
  data_source: DataSource;
  generated_at: string;
}

export interface Explanation {
  factor_name: string;
  factor_value: number;
  contribution_minutes: number;
  direction: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  description: string;
}

export interface WeatherResponse {
  station_id: number;
  station_code: string;
  station_name: string;
  latitude: number;
  longitude: number;
  current?: WeatherObservation;
  forecast: WeatherForecast[];
  data_source: DataSource;
  last_updated: string;
}

export interface WeatherObservation {
  id: number;
  station_id: number;
  temperature_celsius: number;
  feels_like_celsius?: number;
  humidity_percent: number;
  pressure_hpa?: number;
  wind_speed_kmh: number;
  wind_direction_degrees?: number;
  wind_gust_kmh?: number;
  visibility_km?: number;
  cloud_cover_percent?: number;
  weather_condition: string;
  weather_description: string;
  weather_icon?: string;
  precipitation_mm?: number;
  precipitation_probability?: number;
  severity: WeatherSeverity;
  observed_at: string;
  source: string;
}

export interface WeatherForecast {
  id: number;
  station_id: number;
  forecast_time: string;
  temperature_celsius: number;
  weather_condition: string;
  weather_description: string;
  precipitation_probability?: number;
  severity: WeatherSeverity;
}

export type WeatherSeverity = 'NORMAL' | 'CAUTION' | 'SEVERE';

export interface StationReport {
  id: number;
  train_id: number;
  station_id: number;
  event_type: StationReportEventType;
  severity: StationSeverity;
  description: string;
  start_time: string;
  expected_resolution?: string;
  actual_resolution?: string;
  status: StationReportStatus;
  delay_impact_minutes?: number;
  created_at: string;
  updated_at: string;
}

export type StationReportEventType =
  | 'SIGNAL_WAIT'
  | 'PLATFORM_OCCUPIED'
  | 'PRECEDING_TRAIN'
  | 'CROSSING_TRAIN'
  | 'CREW_CHANGE'
  | 'TECHNICAL_CHECK'
  | 'PASSENGER_ASSISTANCE'
  | 'MEDICAL_EMERGENCY'
  | 'TRACK_WORK'
  | 'MAINTENANCE_BLOCK'
  | 'LOCOMOTIVE_ISSUE'
  | 'COACH_ISSUE'
  | 'WATER_CLEANING'
  | 'WEATHER'
  | 'SECURITY_CHECK'
  | 'OPERATIONAL_HOLD'
  | 'OTHER';

export type StationReportStatus = 'PENDING' | 'VERIFIED' | 'PUBLISHED' | 'RESOLVED' | 'CANCELLED';

export type StationSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Alert {
  id: number;
  train_id?: number;
  station_id?: number;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  predicted_impact_minutes?: number;
  confidence?: number;
  is_active: boolean;
  is_acknowledged: boolean;
  created_at: string;
}

export type AlertType =
  | 'DESTINATION_DELAY'
  | 'HIGH_CONGESTION'
  | 'EXTENDED_HALT'
  | 'WEATHER_RISK'
  | 'SPEED_ANOMALY'
  | 'DELAY_PROPAGATION'
  | 'TRAIN_RECOVERY'
  | 'CONNECTION_RISK'
  | 'ROUTE_DEVIATION'
  | 'OPERATIONAL_ANOMALY';

export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface CongestionState {
  id: number;
  section_id?: number;
  station_id?: number;
  train_count: number;
  train_density_per_km: number;
  avg_speed_kmh?: number;
  avg_delay_minutes: number;
  level: CongestionLevel;
  measured_at: string;
}

export type CongestionLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface SimulationStatus {
  is_running: boolean;
  is_paused: boolean;
  speed: number;
  scenario: SimulationScenario;
  active_trains: number;
  current_simulation_time: string;
  last_update: string;
}

export type SimulationScenario =
  | 'NORMAL'
  | 'CONGESTION'
  | 'SIGNAL_DELAY'
  | 'EXTENDED_HALT'
  | 'SPEED_RESTRICTION'
  | 'HEAVY_RAIN'
  | 'LOW_VISIBILITY'
  | 'PRECEDING_TRAIN_DELAY'
  | 'UNSCHEDULED_STOP'
  | 'CASCADING_DELAY'
  | 'RECOVERY';

export type DataSource = 'LIVE' | 'CACHED' | 'SIMULATION' | 'ESTIMATED' | 'GPS_DERIVED' | 'WEATHER_API' | 'SIH_ETA_CORE';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ListResponse<T> {
  trains?: T[];
  stations?: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
  redis: string;
  timestamp: string;
}

export interface SIHUpcomingStation {
  station_code: string;
  station_name: string;
  route_position: number;
  scheduled_remaining_minutes: number;
  predicted_remaining_minutes: number;
  predicted_arrival_delay_minutes: number;
  predicted_eta: string;
}

export interface SIHETAResponse {
  train_number: string;
  train_name: string;
  current_station: string;
  current_station_name?: string;
  current_route_position: number;
  current_delay_minutes: number;
  current_time?: string;
  destination_station?: string;
  destination_station_name?: string;
  predicted_arrival_delay_minutes: number;
  predicted_arrival_time: string;
  predicted_remaining_minutes: number;
  upcoming_station_count: number;
  upcoming_stations: SIHUpcomingStation[];
  confidence_score?: number;
  confidence_level?: string;
  impact_severity?: string;
  delay_trend?: string;
  route_impact?: string;
  model_type?: string;
  model_version?: string;
  data_source: DataSource;
  position_source?: string;
  generated_at: string;
}

export type CoPilotReportReason =
  | 'SIGNAL_ISSUE'
  | 'TRACK_OBSTRUCTION'
  | 'TECHNICAL_ISSUE'
  | 'OPERATIONAL_ISSUE'
  | 'PASSENGER_RELATED'
  | 'WEATHER_RELATED'
  | 'OTHER';

export type CoPilotReportPriority = 'LOW' | 'MEDIUM' | 'HIGH';

export type CoPilotReportStatus = 'NEW' | 'ACKNOWLEDGED' | 'CLOSED';

export interface CoPilotReport {
  id: number;
  train_id?: number;
  user_id: number;
  station_id?: number;
  train_number: string;
  station_code?: string;
  reason: CoPilotReportReason;
  priority: CoPilotReportPriority;
  message: string;
  current_delay_minutes: number;
  status: CoPilotReportStatus;
  is_active: boolean;
  acknowledged_by?: number;
  acknowledged_at?: string;
  closed_by?: number;
  closed_at?: string;
  created_at: string;
  updated_at: string;
  reporter_call_sign?: string;
}

export interface CoPilotReportCreate {
  train_number: string;
  station_code?: string;
  reason: CoPilotReportReason;
  priority: CoPilotReportPriority;
  message: string;
  current_delay_minutes: number;
}