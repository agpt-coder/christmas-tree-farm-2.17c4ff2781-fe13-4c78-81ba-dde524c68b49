from datetime import datetime
from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from pydantic import BaseModel


class Schedule(BaseModel):
    """
    Schedule model specifying events and timings for the staff.
    """

    event: str
    scheduledAt: datetime
    description: Optional[str] = None


class Payroll(BaseModel):
    """
    Payroll details including periods and amounts.
    """

    period: str
    amount: float
    processed: datetime


class GetStaffDetailsResponse(BaseModel):
    """
    Response model containing detailed information about the staff member, including roles, schedules, and payroll information.
    """

    id: int
    username: str
    roles: List[str]
    employmentHistory: List[str]
    currentSchedule: Schedule
    performanceEvaluations: List[str]
    payrollDetails: Payroll


async def get_current_active_user() -> prisma.models.User:
    """
    Stub function to simulate retrieving the currently authenticated user.
    Must be replaced with the actual dependency logic depending on the authentication system in use.
    """
    user = await prisma.models.User.prisma().find_first()
    if not user or user.disabled:
        raise HTTPException(status_code=404, detail="User not found or not active.")
    return user


async def retrieveStaffMember(
    staffId: int,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> GetStaffDetailsResponse:
    """
    Retrieves detailed information about a specific staff member using the staff ID.
    This includes comprehensive data like employment history, role-specific details, and performance evaluations.
    Ensures that the user has the right access permissions before retrieving data.

    Args:
        staffId (int): The unique identifier of the staff member.
        current_user (prisma.models.User): The current user making the request, authenticated and injected by FastAPI's dependency system.

    Returns:
        GetStaffDetailsResponse: Response model containing detailed information about the staff member,
                                 including roles, schedules, and payroll information.

    Raises:
        HTTPException: If the current user does not have sufficient permissions or if the staff member does not exist.
    """
    if current_user.role not in [
        prisma.enums.Role.HumanResourcesManager,
        prisma.enums.Role.Admin,
    ]:
        raise HTTPException(
            status_code=403, detail="Access denied: Insufficient permissions."
        )
    staff_user = await prisma.models.User.prisma().find_unique(
        where={"id": staffId},
        include={"profiles": True, "Schedule": True, "Payroll": True},
    )
    if not staff_user:
        raise HTTPException(status_code=404, detail="Staff member not found.")
    if not staff_user.profiles:
        raise HTTPException(
            status_code=404, detail="Profile details not found for the staff member."
        )
    profile = staff_user.profiles[0]
    schedule = staff_user.Schedule[0] if staff_user.Schedule else None
    payroll = staff_user.Payroll[0] if staff_user.Payroll else None
    return GetStaffDetailsResponse(
        id=staff_user.id,
        username=staff_user.username,
        roles=[staff_user.role.name] if staff_user.role else [],
        employmentHistory=[
            "Worked as {} since {}".format(profile.firstName, profile.lastName)
        ],
        currentSchedule=Schedule(
            event=schedule.event if schedule else "No scheduled events",
            scheduledAt=schedule.scheduledAt if schedule else None,
            description=schedule.description if schedule else "No description",
        ),
        performanceEvaluations=["Performance evaluations records not available."],
        payrollDetails=Payroll(
            period=payroll.period if payroll else "No payroll record",
            amount=float(payroll.amount) if payroll else 0.0,
            processed=payroll.processed if payroll else None,
        ),
    )
