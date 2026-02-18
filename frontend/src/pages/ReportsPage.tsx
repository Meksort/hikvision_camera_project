import React, { useState, useEffect } from 'react';
import { departmentsApi } from '../api/client';
import { Department, DepartmentEmployee } from '../types';
import './ReportsPage.css';

interface Employee {
  id: number;
  hikvision_id: string;
  name: string;
}

const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState<'employee' | 'attendance'>('employee');
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [selectedDepartments, setSelectedDepartments] = useState<number[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [employeeSearch, setEmployeeSearch] = useState('');
  const [departmentSearch, setDepartmentSearch] = useState('');
  const [showEmployeeDropdown, setShowEmployeeDropdown] = useState(false);
  const [showDepartmentDropdown, setShowDepartmentDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDepartments();
    setDefaultDates();
  }, []);

  const setDefaultDates = () => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    setStartDate(formatDateTimeLocal(today));
    setEndDate(formatDateTimeLocal(tomorrow));
  };

  const formatDateTimeLocal = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const loadDepartments = async () => {
    try {
      setLoading(true);
      const data = await departmentsApi.getDepartments();
      setDepartments(data);
    } catch (error) {
      console.error('Ошибка загрузки отделов:', error);
      alert('Не удалось загрузить список сотрудников. Пожалуйста, обновите страницу.');
    } finally {
      setLoading(false);
    }
  };

  const getAllEmployees = (depts: Department[]): Employee[] => {
    const allEmployees: Employee[] = [];
    
    const collectEmployees = (dept: Department) => {
      if (dept.employees && dept.employees.length > 0) {
        dept.employees.forEach((emp: DepartmentEmployee) => {
          allEmployees.push({
            id: emp.id,
            hikvision_id: emp.hikvision_id,
            name: emp.name,
          });
        });
      }
      if (dept.children && dept.children.length > 0) {
        dept.children.forEach((child: Department) => collectEmployees(child));
      }
    };
    
    depts.forEach(dept => collectEmployees(dept));
    return allEmployees;
  };

  const getFilteredEmployees = (): Employee[] => {
    const allEmployees = getAllEmployees(departments);
    if (!employeeSearch.trim()) {
      return allEmployees.sort((a, b) => a.name.localeCompare(b.name));
    }
    
    const search = employeeSearch.toLowerCase();
    return allEmployees
      .filter(emp => 
        emp.name.toLowerCase().includes(search) ||
        emp.hikvision_id.toLowerCase().includes(search)
      )
      .sort((a, b) => a.name.localeCompare(b.name));
  };

  const handleEmployeeSelect = (employee: Employee) => {
    setSelectedEmployee(employee);
    setShowEmployeeDropdown(false);
  };

  const handleDepartmentToggle = (deptId: number) => {
    setSelectedDepartments(prev => {
      if (prev.includes(deptId)) {
        return prev.filter(id => id !== deptId);
      } else {
        return [...prev, deptId];
      }
    });
  };

  const exportReport = () => {
    if (reportType === 'employee') {
      if (!selectedEmployee) {
        alert('Пожалуйста, выберите сотрудника');
        return;
      }
      const params = new URLSearchParams();
      params.append('hikvision_id', selectedEmployee.hikvision_id);
      if (startDate) {
        const startDateStr = startDate.replace('T', ' ') + ':00';
        params.append('start_date', startDateStr);
      }
      if (endDate) {
        const endDateStr = endDate.replace('T', ' ') + ':00';
        params.append('end_date', endDateStr);
      }
      const url = `/api/v1/camera-events/export-excel/?${params.toString()}`;
      window.location.href = url;
    } else {
      if (selectedDepartments.length === 0) {
        alert('Пожалуйста, выберите хотя бы одно подразделение');
        return;
      }
      const params = new URLSearchParams();
      selectedDepartments.forEach(deptId => {
        params.append('department_id', deptId.toString());
      });
      if (startDate) {
        const startDateStr = startDate.split('T')[0];
        params.append('start_date', startDateStr);
      }
      if (endDate) {
        const endDateStr = endDate.split('T')[0];
        params.append('end_date', endDateStr);
      }
      const url = `/api/v1/attendance-stats/export-excel/?${params.toString()}`;
      window.location.href = url;
    }
  };

  const renderDepartmentTree = (depts: Department[], level = 0): React.ReactNode => {
    const filtered = depts.filter(dept => {
      if (!departmentSearch.trim()) return true;
      const search = departmentSearch.toLowerCase();
      const fullPath = dept.full_path || dept.name || '';
      return fullPath.toLowerCase().includes(search);
    });

    return filtered.map(dept => {
      const isSelected = selectedDepartments.includes(dept.id);
      const fullPath = dept.full_path || dept.name || '';
      
      return (
        <div key={dept.id} className="tree-item" style={{ paddingLeft: `${level * 20 + 12}px` }}>
          <div 
            className={`tree-item-icon checkbox ${isSelected ? 'checked' : ''}`}
            onClick={() => handleDepartmentToggle(dept.id)}
          />
          <div className="tree-item-icon folder">📁</div>
          <div className="tree-item-text">{fullPath}</div>
        </div>
      );
    });
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.employee-selector') && !target.closest('.department-selector')) {
        setShowEmployeeDropdown(false);
        setShowDepartmentDropdown(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <div className="reports-page">
      <div className="reports-container">
        <h1>📊 Экспорт отчетов</h1>
        
        <div className="form-group">
          <label>
            <input
              type="radio"
              name="report_type"
              value="employee"
              checked={reportType === 'employee'}
              onChange={() => setReportType('employee')}
            />
            Отчет по сотруднику
          </label>
          <label style={{ marginLeft: '20px' }}>
            <input
              type="radio"
              name="report_type"
              value="attendance"
              checked={reportType === 'attendance'}
              onChange={() => setReportType('attendance')}
            />
            Отчет по посещаемости (по подразделениям)
          </label>
        </div>

        {reportType === 'employee' && (
          <div className="form-group">
            <label>Выберите сотрудника:</label>
            <div className="employee-selector">
              <button
                type="button"
                className={`employee-selector-button ${selectedEmployee ? 'selected' : ''}`}
                onClick={() => setShowEmployeeDropdown(!showEmployeeDropdown)}
              >
                <span>{selectedEmployee ? selectedEmployee.name : 'Нажмите для выбора сотрудника'}</span>
                <span>▼</span>
              </button>
              {showEmployeeDropdown && (
                <div className="employee-selector-dropdown">
                  <div className="employee-selector-search">
                    <input
                      type="text"
                      placeholder="Поиск..."
                      value={employeeSearch}
                      onChange={(e) => setEmployeeSearch(e.target.value)}
                    />
                  </div>
                  <div className="employee-selector-tree">
                    {loading ? (
                      <div className="tree-item" style={{ color: '#888', padding: '20px', textAlign: 'center' }}>
                        Загрузка...
                      </div>
                    ) : getFilteredEmployees().length === 0 ? (
                      <div className="tree-item" style={{ color: '#888', padding: '20px', textAlign: 'center' }}>
                        Сотрудники не найдены
                      </div>
                    ) : (
                      getFilteredEmployees().map(emp => (
                        <div
                          key={emp.id}
                          className={`tree-item ${selectedEmployee?.hikvision_id === emp.hikvision_id ? 'selected' : ''}`}
                          onClick={() => handleEmployeeSelect(emp)}
                        >
                          <div className={`tree-item-icon checkbox ${selectedEmployee?.hikvision_id === emp.hikvision_id ? 'checked' : ''}`} />
                          <div className="tree-item-icon user">👤</div>
                          <div className="tree-item-text">{emp.name}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            {selectedEmployee && (
              <div className="selected-employee-info">
                <strong>Выбран:</strong> {selectedEmployee.name} ({selectedEmployee.hikvision_id})
              </div>
            )}
          </div>
        )}

        {reportType === 'attendance' && (
          <div className="form-group">
            <label>Выберите подразделения:</label>
            <div className="department-selector">
              <button
                type="button"
                className={`employee-selector-button ${selectedDepartments.length > 0 ? 'selected' : ''}`}
                onClick={() => setShowDepartmentDropdown(!showDepartmentDropdown)}
              >
                <span>
                  {selectedDepartments.length > 0
                    ? `Выбрано: ${selectedDepartments.length} подразделений`
                    : 'Нажмите для выбора подразделений'}
                </span>
                <span>▼</span>
              </button>
              {showDepartmentDropdown && (
                <div className="employee-selector-dropdown">
                  <div className="employee-selector-search">
                    <input
                      type="text"
                      placeholder="Поиск подразделений..."
                      value={departmentSearch}
                      onChange={(e) => setDepartmentSearch(e.target.value)}
                    />
                  </div>
                  <div className="employee-selector-tree">
                    {loading ? (
                      <div className="tree-item" style={{ color: '#888', padding: '20px', textAlign: 'center' }}>
                        Загрузка...
                      </div>
                    ) : departments.length === 0 ? (
                      <div className="tree-item" style={{ color: '#888', padding: '20px', textAlign: 'center' }}>
                        Нет данных
                      </div>
                    ) : (
                      renderDepartmentTree(departments)
                    )}
                  </div>
                </div>
              )}
            </div>
            {selectedDepartments.length > 0 && (
              <div className="selected-employee-info">
                <strong>Выбрано подразделений:</strong> {selectedDepartments.length}
              </div>
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="start_date">С какого времени:</label>
          <input
            type="datetime-local"
            id="start_date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="end_date">По какое время:</label>
          <input
            type="datetime-local"
            id="end_date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <div className="button-group">
          <button type="button" className="btn-secondary" onClick={exportReport}>
            📊 Получить отчет
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;

