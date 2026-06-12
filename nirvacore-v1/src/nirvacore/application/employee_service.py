"""Employee use cases."""
from __future__ import annotations

from nirvacore.domain.employee import Employee, Role
from nirvacore.domain.errors import NotFound
from nirvacore.domain.ids import EmployeeId, new_employee_id

from .ports import Clock, EmployeeRepository


class EmployeeService:
    def __init__(self, employees: EmployeeRepository, clock: Clock) -> None:
        self._employees = employees
        self._clock = clock

    def hire(self, full_name: str, role: Role) -> Employee:
        employee = Employee(
            id=new_employee_id(),
            full_name=full_name.strip(),
            role=role,
            hired_on=self._clock.now().date(),
        )
        self._employees.add(employee)
        return employee

    def deactivate(self, employee_id: EmployeeId) -> Employee:
        employee = self._require(employee_id)
        employee.deactivate()
        self._employees.save(employee)
        return employee

    def list_active(self) -> list[Employee]:
        return self._employees.list_active()

    def _require(self, employee_id: EmployeeId) -> Employee:
        employee = self._employees.get(employee_id)
        if employee is None:
            raise NotFound(f"employee {employee_id} not found")
        return employee
