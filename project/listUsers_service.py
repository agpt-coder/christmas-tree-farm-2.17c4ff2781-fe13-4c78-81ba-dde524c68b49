from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


async def get_current_active_user():  # type: ignore
    """
    Stub for dependency that retrieves the currently active user.

    This function is meant to simulate retrieving an authenticated and active user from a request or session.
    """
    pass


class UserListResponse(BaseModel):
    """
    A response structure that may present a list of users or a status message.
    """

    users: List[prisma.models.User]
    message: Optional[str] = None


async def listUsers(
    role: Optional[prisma.enums.Role],
    status: Optional[bool],
    name: Optional[str],
    page: int,
    limit: int,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> UserListResponse:
    """
    Lists all users with filters and pagination. Filters can be applied based on role, status (active or inactive), and name (substring match).
    Current active user is verified before accessing user data. Paginated response is controlled by 'page' and 'limit' parameters.

    Args:
        role (Optional[prisma.enums.Role]): Filter by specific user role (e.g., Admin, SalesManager).
        status (Optional[bool]): Filter by user's active status (True for active).
        name (Optional[str]): Filter by substring of user's name.
        page (int): Specifies the page number of the result set.
        limit (int): Specifies the number of records in a single page.
        current_user (Annotated[prisma.models.User, Depends]): The current active user, injected by FastAPI's dependency system.

    Returns:
        UserListResponse: Contains a list of users or a message if no users found.
    """
    if current_user.disabled:
        return UserListResponse(
            users=[], message="Access denied: Current user is disabled."
        )
    query_filters = {}
    if role:
        query_filters["role"] = role
    if status is not None:
        query_filters["disabled"] = not status
    if name:
        query_filters["username"] = {"contains": name, "mode": "insensitive"}
    skip = (page - 1) * limit
    users = await prisma.models.User.prisma().find_many(
        where=query_filters, skip=skip, take=limit, include={"profiles": True}
    )
    message = "No users found" if not users else None
    return UserListResponse(users=users, message=message)
