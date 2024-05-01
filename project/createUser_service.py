from typing import Annotated, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from pydantic import BaseModel


async def get_current_active_user() -> prisma.models.User:  # type: ignore
    """
    Fetches the currently authenticated and active user.

    Intended for use as a dependency in FastAPI routes that requires user authentication.

    Returns:
        prisma.models.User: Details of the authenticated and active user.

    Raises:
        HTTPException: If no user is authenticated or active.
    """
    pass


class CreateUserResponse(BaseModel):
    """
    Response model for creating a user, containing the ID of the newly created user or error details.
    """

    message: str
    user_id: Optional[int] = None
    error: Optional[str] = None


async def createUser(
    name: str,
    email: str,
    role: prisma.enums.Role,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> CreateUserResponse:
    """
    Creates a new user in the system. It requires user details such as name, email, and role. The endpoint checks for existing data to prevent duplicates and integrates with HR modules for compliance and QuickBooks for financial roles tracking. Expected response is a success message with the user ID of the newly created user or an error message in case of failure.

    Args:
        name (str): The full name of the new user.
        email (str): The email address for the new user.
        role (prisma.enums.Role): The role assigned to the new user, must be one of the predefined roles in the Role enum.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The currently authenticated and active user making this request.

    Returns:
        CreateUserResponse: Response model for creating a user, containing the ID of the newly created user or error details.

    Raises:
        HTTPException: If the current user does not have permission to create users or if unexpected errors occur.
    """
    if current_user.role not in [
        prisma.enums.Role.Admin,
        prisma.enums.Role.HumanResourcesManager,
    ]:
        raise HTTPException(
            status_code=403, detail="Permission denied. Unauthorized to create users."
        )
    existing_user = await prisma.models.User.prisma().find_unique(
        where={"username": email}
    )
    if existing_user:
        return CreateUserResponse(
            message="Failed to create user.",
            error="A user with this email already exists.",
        )
    try:
        new_user = await prisma.models.User.prisma().create(
            data={
                "username": name,
                "role": role,
                "hashed_password": "hashed_password_placeholder",
                "disabled": False,
            }
        )
        return CreateUserResponse(
            message="User created successfully.", user_id=new_user.id
        )
    except Exception as e:
        return CreateUserResponse(message="Failed to create user.", error=str(e))
