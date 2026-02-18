import axios from 'axios';
import { AttendanceStatsResponse, Department, TopLateEmployeesResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const attendanceApi = {
  getStats: async (params?: {
    start_date?: string;
    end_date?: string;
    department?: number[];
  }): Promise<AttendanceStatsResponse> => {
    const queryParams = new URLSearchParams();
    
    if (params?.start_date) {
      queryParams.append('start_date', params.start_date);
    }
    if (params?.end_date) {
      queryParams.append('end_date', params.end_date);
    }
    if (params?.department) {
      params.department.forEach((deptId) => {
        queryParams.append('department', deptId.toString());
      });
    }
    
    const url = `attendance-stats/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await apiClient.get<AttendanceStatsResponse>(url);
    return response.data;
  },
};

export const departmentsApi = {
  getDepartments: async (): Promise<Department[]> => {
    const response = await apiClient.get<Department[]>('departments/');
    return response.data;
  },
};

export const topLateEmployeesApi = {
  getTopLate: async (limit: number = 10): Promise<TopLateEmployeesResponse> => {
    const response = await apiClient.get<TopLateEmployeesResponse>(`top-late-employees/?limit=${limit}`);
    return response.data;
  },
};

export default apiClient;

