from typing import Annotated, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


async def get_current_active_user() -> prisma.models.User:  # type: ignore
    """
    Simulates obtaining the current active user from a session or token.
    Turns the currently authenticated user's user object from Token.
    """
    pass


async def updateUser(
    userId: int,
    username: Optional[str],
    role: Optional[prisma.enums.Role],
    email: Optional[str],
    phone: Optional[str],
    disabled: Optional[bool],
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> UpdateUserResponse:  # TODO(autogpt): F821 Undefined name `UpdateUserResponse`
    """
    Updates existing user information. It accepts partial or full user details for update operations, like updating roles, contact info, etc. The system will validate changes against current roles and business rules. Expected response is a confirmation of the update or an error message.

    Args:
        userId (int): The unique identifier of the user to be updated.
        username (Optional[str]): Updated username for the user.
        role (Optional[Role]): Updated role for the user.
        email (Optional[str]): Updated email address for the user.
        phone (Optional[str]): Updated phone number for the user.
        disabled (Optional[bool]): Flag to disable or enable the user account.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The current user performing the operation, as a security role check.

    Returns:
        UpdateUserResponse: Response model indicating the success or failure of the user update operation.
    """
    if current_user.role != prisma.enums.Role.Admin:
        return UpdateUserResponse(
            success=False,
            message="Authorization error: Only an Admin can update user details.",
        )
    user = await prisma.models.User.prisma().find_unique(where={"id": userId})
    if not user:
        return UpdateUserResponse(
            success=False, message="prisma.models.User not found."
        )
    update_data = {}
    if username is not None:
        update_data["username"] = username
    if role is not None:
        update_data["role"] = role
    if email is not None:
        update_data["profiles"] = {"update": {"email": email}}
    if phone is not None:
        update_data["profiles"] = {"update": {"phone": phone}}
    if disabled is not None:
        update_data["disabled"] = disabled
    updated_user = await prisma.models.User.prisma().update(
        where={"id": userId}, data=update_data, include={"profiles": True}
    )
    return UpdateUserResponse(
        success=True,
        message="prisma.models.User updated successfully.",
        updatedUser=updated_user,
    )


class UpdateUserResponse(BaseModel):
    """
    Response model indicating the success or failure of the user update operation. Includes updated user details on success.
    """

    success: bool
    message: str
    updatedUser: Optional[prisma.models.User] = None
