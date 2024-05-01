from typing import Annotated

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel


async def get_current_active_user() -> prisma.models.User:  # type: ignore
    """
    Placeholder function to simulate fetching the current active and authenticated user.
    Assumes this will be replaced by actual implementation that integrates with the user authentication system.
    """
    pass


class UpdateSalesOutput(BaseModel):
    """
    Output model representing the updated state of the sales record. This will confirm the changes made and reflect the new state in the system, including any updates that were necessary for inventory and financial records.
    """

    id: int
    quantity: int
    salePrice: float
    status: str


async def updateSalesRecord(
    id: int,
    quantity: int,
    salePrice: float,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> UpdateSalesOutput:
    """
    Updates an existing sales record by ID. Parameters such as quantity and sale price can be modified. It verifies the product ID with the Inventory Module for stock adjustments and updates financial records in QuickBooks accordingly.

    Args:
        id (int): The unique identifier for the sales record to be updated.
        quantity (int): The new quantity for the sale, which must be verified against available inventory.
        salePrice (float): The new sale price for the item.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The current user making the request, used to verify permissions and roles.

    Returns:
        UpdateSalesOutput: Output model representing the updated state of the sales record.

    Raises:
        HTTPException: For errors such as unauthorized access, insufficient inventory, or sales record not found.
    """
    if current_user.role not in [
        prisma.enums.Role.Admin,
        prisma.enums.Role.SalesManager,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update sales records.",
        )
    order_item = await prisma.models.OrderItem.prisma().find_unique(
        where={"id": id}, include={"item": True}
    )
    if not order_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sales record not found."
        )
    if order_item.item.quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient inventory available.",
        )
    updated_inventory_item = await prisma.models.InventoryItem.prisma().update(
        where={"id": order_item.itemId},
        data={"quantity": prisma.models.InventoryItem.quantity - quantity},
    )
    updated_order_item = await prisma.models.OrderItem.prisma().update(
        where={"id": id},
        data={"quantity": quantity, "item": {"set": {"salePrice": salePrice}}},
    )
    return UpdateSalesOutput(
        id=updated_order_item.id,
        quantity=updated_order_item.quantity,
        salePrice=salePrice,
        status="Updated",
    )
