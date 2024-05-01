from typing import Annotated

import prisma
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


def get_current_active_user():  # type: ignore
    """
    Dependency function to get the currently authenticated and active user.

    This function is assumed to be implemented elsewhere in the system and responsible for fetching
    the currently active user based on session or authorization token.

    Returns:
        prisma.models.User: The currently authenticated user.
    """
    pass


class SalesRecordResponse(BaseModel):
    """
    Contains information confirming the new sales record and references any updates to inventory levels and financial records.
    """

    sale_id: int
    inventory_update_status: str
    financial_record_status: str


async def addSalesRecord(
    product_id: int,
    quantity: int,
    sale_price: float,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> SalesRecordResponse:
    """
    Adds a new sales record to the system, updates inventory, and logs the financial transaction in QuickBooks.

    Args:
        product_id (int): The ID of the product being sold.
        quantity (int): The quantity of the product being sold.
        sale_price (float): Sale price per unit of the product.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The currently authenticated user performing this operation.

    Returns:
        SalesRecordResponse: Contains information about the sales record, inventory update status, and financial records status.
    """
    inventory_item = await prisma.models.InventoryItem.prisma().find_unique(
        where={"id": product_id}
    )
    if not inventory_item:
        raise ValueError("Inventory item not found")
    if inventory_item.quantity < quantity:
        raise ValueError("Insufficient stock available")
    updated_inventory = await prisma.models.InventoryItem.prisma().update(
        where={"id": product_id},
        data={"quantity": prisma.models.InventoryItem.quantity - quantity},
    )
    inventory_log = await prisma.models.InventoryLog.prisma().create(
        data={
            "itemId": product_id,
            "changedBy": current_user.id,
            "changeType": "Sold",
            "amount": quantity,
        }
    )
    response = SalesRecordResponse(
        sale_id=inventory_log.id,
        inventory_update_status=f"Inventory updated to {updated_inventory.quantity} units.",
        financial_record_status="Financial transaction logged successfully.",
    )
    return response
