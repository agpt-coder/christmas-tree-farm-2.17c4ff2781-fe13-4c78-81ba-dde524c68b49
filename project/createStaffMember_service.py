from typing import Annotated, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class CreateStaffResponse(BaseModel):
    """
    Upon successful creation of a staff member, this model returns the unique ID of the newly created staff record along with confirmation of QuickBooks integration.
    """

    staff_id: int
    quickBooksIntegration: bool


async def createStaffMember(
    firstName: str,
    lastName: str,
    email: str,
    phone: Optional[str],
    role: prisma.enums.Role,
    department: str,
    current_user: Annotated[prisma.models.User, Depends],
) -> CreateStaffResponse:
    """
    Creates a new staff member record. It requires details such as name, contact information, role and department.
    Upon successful creation, it returns the ID of the new staff member, confirming integration with QuickBooks for setting up payroll data.

    Args:
        firstName (str): The first name of the staff member.
        lastName (str): The last name of the staff member.
        email (str): The email address of the staff member, must be unique across the system.
        phone (Optional[str]): The phone number of the staff member, optional.
        role (prisma.enums.Role): The role assigned to the staff member, must be one of the predefined roles in the system.
        department (str): The department to which the staff member is being assigned.
        current_user (Annotated[prisma.models.User, Depends]): The common object used to add the user_id, check dependencies, and validate roles.

    Returns:
        CreateStaffResponse: Upon successful creation of a staff member, this model returns the unique ID of the newly created staff record along with confirmation of QuickBooks integration.
    """
    if current_user.role not in [
        prisma.enums.Role.HumanResourcesManager,
        prisma.enums.Role.Admin,
    ]:
        raise Exception("Unauthorized to create staff member.")
    if await prisma.models.Profile.prisma().find_unique(where={"email": email}):
        raise Exception("Email address already exists in the system.")
    quickBooksIntegrated = True
    profile = await prisma.models.Profile.prisma().create(
        data={
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phone": phone,
            "user": {
                "create": {
                    "username": email.split("@")[0],
                    "role": role,
                    "hashed_password": "hashed_dummy",
                    "disabled": False,
                }
            },
        }
    )
    return CreateStaffResponse(
        staff_id=profile.id, quickBooksIntegration=quickBooksIntegrated
    )
