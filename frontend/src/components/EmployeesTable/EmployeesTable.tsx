import React, { useState, useMemo } from 'react';
import { Employee } from '../../types';
import ProgressBar from '../ProgressBar/ProgressBar';
import './EmployeesTable.css';

interface EmployeesTableProps {
  employees: Employee[];
  loading?: boolean;
}

interface GroupedEmployees {
  [department: string]: Employee[];
}

const EmployeesTable: React.FC<EmployeesTableProps> = ({ employees, loading = false }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedDepartments, setExpandedDepartments] = useState<Set<string>>(new Set());

  const groupedEmployees = useMemo(() => {
    const grouped: GroupedEmployees = {};
    
    employees.forEach((employee) => {
      const dept = employee.department || 'Без отдела';
      if (!grouped[dept]) {
        grouped[dept] = [];
      }
      grouped[dept].push(employee);
    });

    // Сортируем отделы и сотрудников
    const sortedGrouped: GroupedEmployees = {};
    Object.keys(grouped)
      .sort()
      .forEach((dept) => {
        sortedGrouped[dept] = grouped[dept].sort((a, b) => a.name.localeCompare(b.name));
      });

    return sortedGrouped;
  }, [employees]);

  const filteredGroupedEmployees = useMemo(() => {
    if (!searchQuery.trim()) {
      return groupedEmployees;
    }

    const query = searchQuery.toLowerCase();
    const filtered: GroupedEmployees = {};

    Object.keys(groupedEmployees).forEach((dept) => {
      const filteredEmployees = groupedEmployees[dept].filter(
        (emp) =>
          emp.name.toLowerCase().includes(query) ||
          emp.position?.toLowerCase().includes(query) ||
          dept.toLowerCase().includes(query)
      );

      if (filteredEmployees.length > 0) {
        filtered[dept] = filteredEmployees;
      }
    });

    return filtered;
  }, [groupedEmployees, searchQuery]);

  const toggleDepartment = (dept: string) => {
    const newExpanded = new Set(expandedDepartments);
    if (newExpanded.has(dept)) {
      newExpanded.delete(dept);
    } else {
      newExpanded.add(dept);
    }
    setExpandedDepartments(newExpanded);
  };

  const formatMinutes = (minutes: number) => {
    if (minutes === 0) return '0м';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}ч ${mins}м`;
    }
    return `${mins}м`;
  };

  if (loading) {
    return (
      <div className="employees-table-loading">
        <div className="loading-spinner" />
        <p>Загрузка данных...</p>
      </div>
    );
  }

  if (employees.length === 0) {
    return (
      <div className="employees-table-empty">
        <p>Нет данных для отображения</p>
      </div>
    );
  }

  return (
    <div className="employees-table-container">
      <div className="employees-table-search">
        <input
          type="text"
          placeholder="Поиск по имени, должности или отделу..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="employees-table">
        <table>
          <thead>
            <tr>
              <th style={{ width: '40%' }}>Отдел / Сотрудник</th>
              <th style={{ width: '30%' }}>Статистика</th>
              <th style={{ width: '15%' }}>Опоздания</th>
              <th style={{ width: '15%' }}>Ранние уходы</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(filteredGroupedEmployees).map((dept) => {
              const deptEmployees = filteredGroupedEmployees[dept];
              const isExpanded = expandedDepartments.has(dept);

              return (
                <React.Fragment key={dept}>
                  <tr className="department-row" onClick={() => toggleDepartment(dept)}>
                    <td colSpan={4}>
                      <div className="department-header">
                        <span className={`expand-icon ${isExpanded ? 'expanded' : ''}`}>
                          ▶
                        </span>
                        <span className="department-name">{dept}</span>
                        <span className="department-count">({deptEmployees.length})</span>
                      </div>
                    </td>
                  </tr>
                  {isExpanded &&
                    deptEmployees.map((employee) => (
                      <tr key={employee.id} className="employee-row">
                        <td>
                          <div className="employee-info">
                            <img
                              src={employee.avatar}
                              alt={employee.name}
                              className="employee-avatar"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(employee.name)}&background=random&size=40`;
                              }}
                            />
                            <div className="employee-details">
                              <div className="employee-name">{employee.name}</div>
                              {employee.position && (
                                <div className="employee-position">{employee.position}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td>
                          <ProgressBar
                            productivePercent={employee.stats.productivePercent}
                            distractionPercent={employee.stats.distractionPercent}
                            idlePercent={employee.stats.idlePercent}
                          />
                        </td>
                        <td>
                          <span className="metric-value">{formatMinutes(employee.lateMinutes)}</span>
                        </td>
                        <td>
                          <span className="metric-value">{formatMinutes(employee.earlyLeaveMinutes)}</span>
                        </td>
                      </tr>
                    ))}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EmployeesTable;

