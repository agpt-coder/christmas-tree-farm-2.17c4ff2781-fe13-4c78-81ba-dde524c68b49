from typing import Annotated, List

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


class CreateRoleResponse(BaseModel):
    """
    Response model returning details of the newly created role.
    """

    id: int
    name: str
    responsibilities: List[str]
    permissions: List[str]
    status: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
) -> prisma.models.User:
    """
    Retrieves the currently authenticated user from the database using the provided token.
    Args:
        token (str): Authentication token.
    Returns:
        prisma.models.User: The authenticated user object.
    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """
    user = await prisma.models.User.prisma().find_first(
        where={"hashed_password": token, "disabled": False}
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user


async def createRole(
    name: str,
    responsibilities: List[str],
    permissions: List[str],
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> CreateRoleResponse:
    """
    Creates a new role in the system. This includes defining the role name, responsibilities, and permissions.
    Helps in customizing staff structure as per organizational needs.

    Args:
        name (str): The name of the new role.
        responsibilities (List[str]): List of responsibilities associated with the role.
        permissions (List[str]): List of permissions granted for this role.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The authenticated user making the request.

    Returns:
        CreateRoleResponse: Response model returning details of the newly created role.
    """
    if current_user.role != prisma.enums.Role.Admin:
        return CreateRoleResponse(
            id=-1,
            name=name,
            responsibilities=responsibilities,
            permissions=permissions,
            status="Failure: User does not have the necessary permissions",
        )
    new_role = await prisma.models.User.prisma().create(
        data={
            "name": name,
            "role": "Admin",
            "profiles": {
                "create": {
                    "responsibilities": responsibilities,
                    "permissions": permissions,
                }
            },
        }
    )
    return CreateRoleResponse(
        id=new_role.id,
        name=new_role.name,
        responsibilities=responsibilities,
        permissions=permissions,
        status="Success",
    )  # TODO(autogpt): Cannot access member "name" for type "User"


#     Member "name" is unknown. reportAttributeAccessIssue
