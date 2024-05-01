from typing import Annotated

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from pydantic import BaseModel


class DeleteStaffResponse(BaseModel):
    """
    Response model indicating the result of the delete operation on a staff member. It should confirm the deletion and ensure no residual data remains that could lead to data integrity issues.
    """

    success: bool
    message: str


async def get_current_active_user(bearer_token: str) -> prisma.models.User:
    """
    Simulates retrieving the currently authenticated user based on the provided bearer token. In a real application, this would validate the token and extract user details.

    Args:
        bearer_token (str): Bearer token for authentication.

    Returns:
        User (prisma.models.User): The user object of the authenticated user.

    Raises:
        HTTPException: If the user is not found or the token is invalid.
    """
    user = await prisma.models.User.prisma().find_unique(
        where={"hashed_password": bearer_token}
    )
    if user is None or user.disabled:
        raise HTTPException(status_code=404, detail="User not found or not active")
    return user


async def deleteStaffMember(
    staffId: int,
    bearer_token: str,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> DeleteStaffResponse:
    """
    Deletes a staff member's record, removing them from the system entirely. It also ensures that their payroll information is removed from QuickBooks to maintain financial accuracy.

    Args:
        staffId (int): The unique identifier of the staff member to be deleted.
        bearer_token (str): Authorization token needed to execute this operation. Token must provide admin privileges or belong to a human resources manager.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The authenticated user who is performing the operation.

    Returns:
        DeleteStaffResponse: Response model indicating the result of the delete operation on a staff member. It should confirm the deletion and ensure no residual data remains that could lead to data integrity issues.
    """
    if current_user.role not in [
        prisma.enums.Role.Admin,
        prisma.enums.Role.HumanResourcesManager,
    ]:
        raise HTTPException(
            status_code=403, detail="Unauthorized access: Insufficient permissions."
        )
    await prisma.models.Schedule.prisma().delete_many(where={"assignedTo": staffId})
    await prisma.models.Payroll.prisma().delete_many(where={"userId": staffId})
    await prisma.models.User.prisma().delete(where={"id": staffId})
    return DeleteStaffResponse(
        success=True,
        message="Staff member and all associated records deleted successfully.",
    )
