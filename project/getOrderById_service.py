from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from pydantic import BaseModel


async def get_current_active_user() -> prisma.models.User:  # type: ignore
    """
    Placeholder function to simulate fetching the current active user.

    Returns:
        prisma.models.User: The currently authenticated user.
    """
    pass


async def getOrderById(
    orderId: int,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> OrderDetailsResponse:  # TODO(autogpt): F821 Undefined name `OrderDetailsResponse`
    """
    Retrieves the detailed information for an order by its ID. Information includes customer details, items in the order,
    total price, and order status. Access is restricted to specific user roles due to sensitive data.

    Args:
        orderId (int): The unique identifier for the order to be retrieved.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The currently active, authenticated user.

    Returns:
        OrderDetailsResponse: The detailed information about the order.

    Raises:
        HTTPException: 403 error if the user does not have proper role permissions
                       404 error if the order does not exist
    """
    required_user_roles = {
        prisma.enums.Role.Admin,
        prisma.enums.Role.SalesManager,
        prisma.enums.Role.CustomerServiceRepresentative,
    }
    if current_user.role not in required_user_roles:
        raise HTTPException(
            status_code=403, detail="Not authorized to access order information."
        )
    order = await prisma.models.Order.prisma().find_unique(
        where={"id": orderId},
        include={"customer": True, "items": {"include": {"item": True}}},
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    customer_info = Customer(
        first_name=order.customer.firstName,
        last_name=order.customer.lastName,
        email=order.customer.email,
        phone=order.customer.phone,
    )
    items_detailed = [
        OrderItemDetailed(
            item_name=i.item.name,
            quantity=i.quantity,
            price=i.item.price if hasattr(i.item, "price") else 0,
        )
        for i in order.items
    ]  # TODO(autogpt): Cannot access member "price" for type "InventoryItem"
    #     Member "price" is unknown. reportAttributeAccessIssue
    total_price = sum((item.price * item.quantity for item in items_detailed))
    order_status = OrderStatus(status=order.status.name)
    return OrderDetailsResponse(
        order_id=order.id,
        customer=customer_info,
        items=items_detailed,
        total_price=total_price,
        status=order_status,
    )


class Customer(BaseModel):
    """
    Data model representing a customer including personal and contact information.
    """

    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None


class OrderItemDetailed(BaseModel):
    """
    Detailed data model for items within the order, including product details and quantity.
    """

    item_name: str
    quantity: int
    price: float


class OrderStatus(BaseModel):
    """
    Describes the status of an order, can be one of several pre-defined states like 'Pending', 'Shipped', etc.
    """

    status: str


class OrderDetailsResponse(BaseModel):
    """
    Response model encapsulating detailed information about an order, including customer info and product details.
    """

    order_id: int
    customer: Customer
    items: List[OrderItemDetailed]
    total_price: float
    status: OrderStatus
