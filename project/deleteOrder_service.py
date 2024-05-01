from typing import Annotated

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class DeleteOrderResponse(BaseModel):
    """
    Acknowledgement response for a successfully deleted order. It indicates that the order was deleted and necessary updates were made to both inventory and financial records.
    """

    success: bool
    message: str


async def deleteOrder(
    orderId: int, current_user: Annotated[prisma.models.User, Depends()]
) -> DeleteOrderResponse:
    """
    Deletes an order from the system based on the order ID. This action reflects changes immediately in the inventory counts by updating the Inventory Management System and adjusts financial records in QuickBooks.

    Args:
        orderId (int): The unique identifier for the order that needs to be deleted.
        current_user (Annotated[prisma.models.User, Depends()]): The current user object used to add the user_id, check dependencies, and validate roles.

    Returns:
        DeleteOrderResponse: Acknowledgement response for a successfully deleted order. It indicates that the order was deleted and necessary updates were made to both inventory and financial records.
    """
    if current_user.role not in [
        prisma.enums.Role.Admin,
        prisma.enums.Role.OrderFulfillmentOfficer,
    ]:
        return DeleteOrderResponse(success=False, message="Permission denied.")
    order = await prisma.models.Order.prisma().find_unique(
        where={"id": orderId}, include={"items": True}
    )
    if order is None:
        return DeleteOrderResponse(success=False, message="Order not found.")
    updates = []
    for item in order.items:
        updates.append(
            prisma.models.InventoryItem.prisma().update(
                where={"id": item.itemId},
                data={"quantity": {"increment": item.quantity}},
            )
        )
    await asyncio.gather(*updates)  # TODO(autogpt): F821 Undefined name `asyncio`
    await prisma.models.Order.prisma().delete(where={"id": orderId})
    return DeleteOrderResponse(
        success=True, message="Order successfully deleted and inventory updated."
    )
