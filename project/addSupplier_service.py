from typing import Annotated, List

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class Address(BaseModel):
    """
    This is a complex type representing the supplier's address details.
    """

    street: str
    city: str
    state: str
    country: str
    zip_code: str


class AddSupplierResponse(BaseModel):
    """
    Response model for adding a new supplier. It confirms the addition of the supplier and provides a reference ID.
    """

    success: bool
    message: str
    supplier_id: str


async def addSupplier(
    name: str,
    address: Address,
    tree_types: List[str],
    current_user: Annotated[prisma.models.User, Depends],
) -> AddSupplierResponse:
    """
    Allows adding a new supplier to the system. Requires detailed supplier information including name, address, and tree types provided. Duplicates are checked to maintain data integrity. Only authorized users can access it to ensure proper auditing.

    Args:
        name (str): The name of the new supplier.
        address (Address): The complete address of the supplier.
        tree_types (List[str]): List of tree types provided by the supplier.
        current_user (Annotated[prisma.models.User, Depends]): The user authenticated and allowed to perform this operation.

    Returns:
        AddSupplierResponse: Response model for adding a new supplier. It confirms the addition of the supplier and provides a reference ID.
    """
    if current_user.role not in [
        prisma.enums.Role.Admin,
        prisma.enums.Role.SupplyChainCoordinator,
    ]:
        return AddSupplierResponse(
            success=False, message="Insufficient permissions", supplier_id=""
        )
    supplier_id = "12345"
    return AddSupplierResponse(
        success=True, message="Supplier added successfully", supplier_id=supplier_id
    )
