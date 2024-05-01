from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class StaffDetail(BaseModel):
    """
    Detailed information of a staff member including their name, role, and contact details.
    """

    id: str
    firstName: str
    lastName: str
    role: prisma.enums.Role
    email: str
    phone: Optional[str] = None


class StaffList(BaseModel):
    """
    A list containing details of staff members, possibly filtered and paginated as per the request. Each entry in the array includes essential details such as name, role, and contact information.
    """

    staff: List[StaffDetail]


async def listStaffMembers(
    current_user: Annotated[prisma.models.User, Depends],
    limit: Optional[int] = None,
    role: Optional[List[prisma.enums.Role]] = None,
    page: Optional[int] = None,
) -> StaffList:
    """
    Retrieves a list of all staff members, including their roles and basic details. It supports filtering and pagination to help manage large datasets. The response includes an array of staff members with information like names, roles, and contact details.

    Args:
        current_user (Annotated[prisma.models.User, Depends]): The current active user authenticated with the system performing the request.
        limit (Optional[int]): Limit on the number of staff member entries per page.
        role (Optional[List[prisma.enums.Role]]): Optional filter by staff role to retrieve specific groups of staff members.
        page (Optional[int]): Page number for pagination purposes.

    Returns:
        StaffList: A list containing details of staff members, possibly filtered and paginated as per the request. Each entry in the array includes essential details such as name, role, and contact information.
    """
    where_filter = {}
    if role:
        where_filter["user"] = {"role": {"in": role}}
    skip = limit * (page - 1) if limit and page else 0
    profiles = await prisma.models.Profile.prisma().find_many(
        where=where_filter, skip=skip, take=limit, include={"user": True}
    )
    staff_details = [
        StaffDetail(
            id=str(profile.id),
            firstName=profile.firstName,
            lastName=profile.lastName,
            role=profile.user.role,
            email=profile.email,
            phone=profile.phone,
        )
        for profile in profiles
    ]
    return StaffList(staff=staff_details)
