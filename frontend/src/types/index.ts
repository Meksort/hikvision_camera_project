export interface AttendanceStatsResponse {
  kpi: {
    workedPercent: number;
    workedTime: string;
    workedSeconds: number;
    productivePercent: number;
    productiveTime: string;
    productiveSeconds: number;
    idlePercent: number;
    idleTime: string;
    idleSeconds: number;
    distractionPercent: number;
    distractionTime: string;
    distractionSeconds: number;
    trend: {
      worked: number;
      productive: number;
      idle: number;
      distraction: number;
    };
  };
  employees: Employee[];
}

export interface Employee {
  id: number;
  name: string;
  avatar: string;
  department: string;
  position: string;
  stats: {
    productivePercent: number;
    distractionPercent: number;
    idlePercent: number;
  };
  lateMinutes: number;
  earlyLeaveMinutes: number;
  incidentsCount: number;
  workedSeconds: number;
}

export interface DepartmentEmployee {
  id: number;
  hikvision_id: string;
  name: string;
  position?: string;
  schedule_type?: string;
  schedule_description?: string;
  allowed_late_minutes?: number;
  allowed_early_leave_minutes?: number;
  department_name?: string;
}

export interface Department {
  id: number;
  name: string;
  full_path: string;
  parent?: number;
  parent_name?: string;
  employees?: DepartmentEmployee[];
  children?: Department[];
  created_at?: string;
  updated_at?: string;
}

export interface FilterParams {
  start_date?: string;
  end_date?: string;
  department?: number[];
}

export interface TopLateEmployee {
  id: number;
  name: string;
  avatar: string;
  department: string;
  position: string;
  lateCount: number;
  earlyLeaveCount: number;
}

export interface TopLateEmployeesResponse {
  employees: TopLateEmployee[];
}
