from datetime import datetime
from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class StaffScheduleDetail(BaseModel):
    """
    Detailed structure for a staff schedule entry including linked user and profile.
    """

    schedule_id: int
    event: str
    scheduled_at: datetime
    staff_name: str
    role: prisma.enums.Role
    department: str


class StaffScheduleResponse(BaseModel):
    """
    Response model containing the list of staff schedules. Each schedule is accompanied by detailed user and profile information.
    """

    schedules: List[StaffScheduleDetail]


async def staffSchedule(
    date: Optional[str],
    role: Optional[prisma.enums.Role],
    department: Optional[str],
    current_user: Annotated[prisma.models.User, Depends],
) -> StaffScheduleResponse:
    """
    Retrieves the work schedules for all staff members. This is crucial for planning and ensuring coverage. Supports filtering by date, role, and departments.

    Args:
        date (Optional[str]): Filter schedules on this date; expected to be in YYYY-MM-DD format.
        role (Optional[prisma.enums.Role]): Filter schedules by staff role.
        department (Optional[str]): Filter schedules by department. Department details are derived from user roles and profiles.
        current_user (Annotated[prisma.models.User, Depends]): The currently authenticated user (assuming to be provided by Depends).

    Returns:
        StaffScheduleResponse: Response model containing the list of staff schedules. Each schedule is accompanied by detailed user and profile information.
    """
    where_clause = {}
    if date:
        where_clause["scheduledAt"] = datetime.strptime(date, "%Y-%m-%d")
    if role:
        where_clause["staff"] = {"role": role}
    if department:
        where_clause["department"] = department
    schedules = await prisma.models.Schedule.prisma().find_many(
        where=where_clause, include={"staff": {"include": {"profiles": True}}}
    )
    schedule_details = []
    for schedule in schedules:
        if schedule.staff and schedule.staff.profiles:
            profile = schedule.staff.profiles[0]
            detail = StaffScheduleDetail(
                schedule_id=schedule.id,
                event=schedule.event,
                scheduled_at=schedule.scheduledAt,
                staff_name=f"{profile.firstName} {profile.lastName}",
                role=schedule.staff.role,
                department=profile.department if profile.department else "Unknown",
            )  # TODO(autogpt): Cannot access member "department" for type "Profile"
            #     Member "department" is unknown. reportAttributeAccessIssue
            schedule_details.append(detail)
    return StaffScheduleResponse(schedules=schedule_details)
