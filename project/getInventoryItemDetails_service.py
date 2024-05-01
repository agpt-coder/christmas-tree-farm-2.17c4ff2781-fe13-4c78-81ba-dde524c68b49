from datetime import datetime
from typing import Annotated, List

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


async def get_current_active_user() -> prisma.models.User:  # type: ignore
    """
    Retrieve and authenticate the current active user.
    This function is a stub to simulate user authentication and retrieval.
    """
    pass


class InventoryItemDetails(BaseModel):
    """
    Details of the requested inventory item including type, name, quantity and unit.
    """

    type: str
    name: str
    quantity: int
    threshold: int
    unit: str


class InventoryLogDetails(BaseModel):
    """
    Log details capturing historical adjustments or usage of the inventory item.
    """

    timestamp: datetime
    changedBy: int
    changeType: str
    amount: int


class SalesDetails(BaseModel):
    """
    Details of sales transactions that involved this inventory item.
    """

    orderId: int
    quantitySold: int


class InventoryItemResponse(BaseModel):
    """
    Provides detailed information on the inventory item, including usage history, inventory adjustments, and linked sales. The output is designed to support audit procedures and detailed inventory tracking.
    """

    itemDetails: InventoryItemDetails
    usageLogs: List[InventoryLogDetails]
    relatedSales: List[SalesDetails]


async def getInventoryItemDetails(
    itemId: int,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> InventoryItemResponse:
    """
    Retrieves detailed information about a specific inventory item, including historical data about usage,
    previous adjustments, and connected sales documents. This function is essential for audits and inventory tracking.

    Args:
        itemId (int): The unique identifier of the inventory item.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The logged-in user object.

    Returns:
        InventoryItemResponse: Detailed information on the inventory item, including usage history,
                               inventory adjustments, and linked sales.
    """
    if current_user.role not in [
        prisma.enums.Role.InventoryManager,
        prisma.enums.Role.Admin,
    ]:
        raise PermissionError("You do not have permission to view inventory details.")
    item = await prisma.models.InventoryItem.prisma().find_unique(where={"id": itemId})
    if not item:
        raise ValueError("Inventory item not found.")
    item_details = InventoryItemDetails(
        type=item.type,
        name=item.name,
        quantity=item.quantity,
        threshold=item.threshold,
        unit=item.unit,
    )
    logs = await prisma.models.InventoryLog.prisma().find_many(where={"itemId": itemId})
    usage_logs = [
        InventoryLogDetails(
            timestamp=log.timestamp,
            changedBy=log.changedBy,
            changeType=log.changeType,
            amount=log.amount,
        )
        for log in logs
    ]
    order_items = await prisma.models.OrderItem.prisma().find_many(
        where={"itemId": itemId}, include={"order": True}
    )
    related_sales = [
        SalesDetails(
            orderId=order_item.order.id if order_item.order else None,
            quantitySold=order_item.quantity,
        )
        for order_item in order_items
        if order_item.order
    ]
    return InventoryItemResponse(
        itemDetails=item_details, usageLogs=usage_logs, relatedSales=related_sales
    )
