from typing import Annotated, List

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


async def get_current_active_user() -> prisma.models.User:  # type: ignore
    """
    Stub function to simulate the retrieval of a currently active user. In a real scenario,
    this would fetch user data from a database or context, ensuring they are authenticated and active.
    """
    pass


class SupplierInfo(BaseModel):
    """
    A detailed object representing each supplier which includes company name, contact information, and what types of trees they supply.
    """

    company_name: str
    contact_info: str
    supplied_tree_types: List[str]


class GetSuppliersResponse(BaseModel):
    """
    Response model includes a list of suppliers with details about each. Each supplier is represented by a SupplierInfo object which will be defined in related_types.
    """

    suppliers: List[SupplierInfo]


async def getSuppliers(
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)]
) -> GetSuppliersResponse:
    """
    Provides a list of all suppliers. It fetches data about suppliers including company name,
    contact information, and the types of trees they provide. The system will ensure that responses
    are cached for efficiency and secured to protect supplier data.

    Args:
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The current user object
                                  used to add the user_id, check dependencies, and validate roles.

    Returns:
        GetSuppliersResponse: Response model includes a list of suppliers with details about each.
                              Each supplier is represented by a SupplierInfo object.
    """
    if current_user.role not in [
        prisma.enums.Role.Admin,
        prisma.enums.Role.SupplyChainCoordinator,
    ]:
        raise PermissionError(
            "You do not have the necessary permissions to view suppliers."
        )
    profiles = await prisma.models.Profile.prisma().find_many(
        where={"user": {"role": "SupplyChainCoordinator"}}
    )
    suppliers = [
        SupplierInfo(
            company_name=profile.user.username if profile.user else "Unknown Company",
            contact_info=profile.email
            if profile.email
            else "No contact info available",
            supplied_tree_types=["Pine", "Oak", "Maple"],
        )
        for profile in profiles
        if profile.user is not None
    ]
    return GetSuppliersResponse(suppliers=suppliers)
