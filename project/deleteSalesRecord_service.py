from typing import Annotated

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class DeleteSalesResponse(BaseModel):
    """
    This response model provides feedback on the operation, detailing whether the sales record was successfully deleted and if the associated adjustments were made.
    """

    success: bool
    message: str


async def deleteSalesRecord(
    id: int, current_user: Annotated[prisma.models.User, Depends]
) -> DeleteSalesResponse:
    """
    Deletes a specified sales record by ID. It will revert the stock level in the Inventory Management Module and make necessary financial adjustments in QuickBooks.

    Args:
        id (int): The unique identifier of the sales record to be deleted.
        current_user (Annotated[prisma.models.User, Depends]): The current user attempting to delete the record, injected dependency to check user context and permissions.

    Returns:
        DeleteSalesResponse: This response model provides feedback on the operation, detailing whether the sales record was successfully deleted and if the associated adjustments were made.
    """
    if current_user.role not in [
        prisma.enums.Role.SalesManager,
        prisma.enums.Role.Admin,
    ]:
        return DeleteSalesResponse(
            success=False, message="Insufficient permission to delete sales records."
        )
    order_item = await prisma.models.OrderItem.prisma().find_unique(where={"id": id})
    if not order_item:
        return DeleteSalesResponse(success=False, message="Sales record not found.")
    inventory_item = await prisma.models.InventoryItem.prisma().find_unique(
        where={"id": order_item.itemId}
    )
    if inventory_item:
        await prisma.models.InventoryItem.prisma().update(
            where={"id": order_item.itemId},
            data={"quantity": {"increment": order_item.quantity}},
        )
        await prisma.models.InventoryLog.prisma().create(
            data={
                "itemId": order_item.itemId,
                "changedBy": current_user.id,
                "changeType": "Adjusted",
                "amount": order_item.quantity,
            }
        )
    await prisma.models.OrderItem.prisma().delete(where={"id": id})
    return DeleteSalesResponse(
        success=True,
        message="Sales record deleted successfully and inventory restored.",
    )
