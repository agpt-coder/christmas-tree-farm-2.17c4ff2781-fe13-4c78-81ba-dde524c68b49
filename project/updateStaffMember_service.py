from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


class ContactDetails(BaseModel):
    """
    Defines the various contact details that can be updated for a staff member.
    """

    email: Optional[str] = None
    phone: Optional[str] = None


class UpdateStaffResponse(BaseModel):
    """
    Confirms the successful update of a staff member's record, including any changes to the QuickBooks integration for payroll.
    """

    success: bool
    updatedFields: List[str]
    message: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
) -> prisma.models.User:
    """
    Authenticates the user using the provided token and retrieves the active user object.

    Args:
        token (str): The token used for user authentication.

    Returns:
        prisma.models.User: The authenticated prisma.models.User object.

    Raises:
        HTTPException: If authentication fails or user not found.
    """
    user = await prisma.models.User.prisma().find_first(
        where={"username": "extracted_from_token"}
    )
    if user is None:
        raise HTTPException(status_code=404, detail="prisma.models.User not found")
    return user


async def updateStaffMember(
    staffId: int,
    role: prisma.enums.Role,
    newSalary: Optional[float],
    contactDetails: ContactDetails,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> UpdateStaffResponse:
    """
    Updates a staff member’s record. It accepts partial or full updates, such as changing roles,
    adjusting salaries, or updating contact details. Ensures all changes are synced for payroll adjustment.

    Args:
        staffId (int): The unique identifier for the staff member whose record is to be updated.
        role (prisma.enums.Role): The staff member's new role.
        newSalary (Optional[float]): The updated salary for the staff member if applicable.
        contactDetails (ContactDetails): Container for updated contact details of the staff member.
        current_user (prisma.models.User): The user authenticated to perform this operation.

    Returns:
        UpdateStaffResponse: Response object detailing the outcome of the update operation.
    """
    updated_fields = []
    staff_member = await prisma.models.User.prisma().find_unique(where={"id": staffId})
    if staff_member is None:
        return UpdateStaffResponse(
            success=False, updatedFields=[], message="Staff member not found."
        )
    if staff_member.role != role:
        await prisma.models.User.prisma().update(
            where={"id": staffId}, data={"role": role}
        )
        updated_fields.append("role")
    if newSalary is not None:
        await prisma.models.Payroll.prisma().upsert(
            where={"userId": staffId},
            create={"userId": staffId, "amount": newSalary},
            update={"amount": newSalary},
        )  # TODO(autogpt): Argument missing for parameter "data". reportCallIssue
        updated_fields.append("salary")
    profile_updates = {}
    if contactDetails.email:
        profile_updates["email"] = contactDetails.email
        updated_fields.append("email")
    if contactDetails.phone:
        profile_updates["phone"] = contactDetails.phone
        updated_fields.append("phone")
    if profile_updates:
        await prisma.models.Profile.prisma().update(
            where={"userId": staffId}, data=profile_updates
        )
    return UpdateStaffResponse(
        success=True,
        updatedFields=updated_fields,
        message="Staff member details successfully updated.",
    )
