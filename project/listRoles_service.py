from typing import Annotated, List

import prisma
import prisma.enums
import prisma.models
from auth_deps import (
    get_current_active_user,
)  # TODO(autogpt): Expression of type "(current_user: User) -> Coroutine[Any, Any, User]" cannot be assigned to declared type "() -> Coroutine[Any, Any, User]"

#     Type "(current_user: User) -> Coroutine[Any, Any, User]" cannot be assigned to type "() -> Coroutine[Any, Any, User]". reportAssignmentType
from fastapi import Depends, HTTPException
from pydantic import BaseModel


class RoleDescription(BaseModel):
    """
    Detailed object containing the role name and its description.
    """

    role_name: str
    description: str


class GetStaffRolesResponse(BaseModel):
    """
    Response model containing a list of all available roles with brief descriptions.
    """

    roles: List[RoleDescription]


async def get_current_active_user() -> prisma.models.User:
    """
    Retrieves the currently authenticated and active user from the database, assuming
    the request context previously authenticated the user and flagged them as active.

    This function assumes an authentication process is in place that sets a context or session
    variable indicating the currently logged in user's ID, and checks that the user is not disabled.

    This is a hypothetical implementation of how one might retrieve currently active user details
    in a real application where the user's session is stored and can be accessed to fetch user details,
    assuming the "User" model has fields 'disabled' reflecting if the user is active.

    Returns:
        prisma.models.User: The user object of the currently authenticated and active user.

    Raises:
        RuntimeError: If no active user is found or the user account is disabled.

    Example:
        # Assuming an application context where the user is authenticated and active
        current_user = await get_current_active_user()
        print(current_user.username)
    """
    user = await prisma.models.User.prisma().find_first(
        where={"disabled": False}, reject_on_not_found=True
    )  # TODO(autogpt): No parameter named "reject_on_not_found". reportCallIssue
    if user is None or user.disabled:
        raise RuntimeError("No active user found or the user account is disabled.")
    return user


def describe_roles() -> List[RoleDescription]:
    """
    Provides descriptions for each staff role stored in the Role enum.

    Returns:
        List[RoleDescription]: List of roles with their names and descriptions.
    """
    return [
        RoleDescription(
            role_name=role.name, description=f"The responsibilities of {role.name}."
        )
        for role in prisma.enums.Role
    ]


async def listRoles(
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)]
) -> GetStaffRolesResponse:
    """
    Lists all available staff roles within the organization. This helps in role assignments and in understanding
    the hierarchy and structure. The function verifies the user's role and provides a response if the user
    has administrative access.

    Args:
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The current active user with
        dependencies checked by get_current_active_user.

    Returns:
        GetStaffRolesResponse: Response model containing a list of all available roles with brief descriptions.

    Example:
        current_user = await get_current_active_user()  # Assume this function resolves to a user with Admin role.
        roles_info = await listRoles(current_user)
        print(roles_info)
    """
    if current_user.role != prisma.enums.Role.Admin:
        raise HTTPException(
            status_code=403, detail="Unauthorized access. User must be an Admin."
        )
    roles_descriptions = describe_roles()
    return GetStaffRolesResponse(roles=roles_descriptions)
