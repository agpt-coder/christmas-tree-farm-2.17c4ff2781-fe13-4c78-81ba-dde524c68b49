from datetime import datetime
from typing import Annotated, Dict, List, Optional

import prisma
import prisma.models
from auth_deps import get_current_active_user
from fastapi import Depends
from pydantic import BaseModel


class OrderStatus(BaseModel):
    """
    Describes the status of an order, can be one of several pre-defined states like 'Pending', 'Shipped', etc.
    """

    status: str


class OrderItemData(BaseModel):
    """
    Descriptive details about individual order items.
    """

    itemId: int
    name: str
    quantity: int


class OrderData(BaseModel):
    """
    Data container for individual orders associated with the customer.
    """

    orderId: int
    status: OrderStatus
    placedAt: datetime
    items: List[OrderItemData]


class CustomerDetailsResponse(BaseModel):
    """
    Outputs detailed information about a customer, such as their preferences, order history, and associated QuickBooks billing.
    """

    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None
    preferences: Dict
    orders: List[OrderData]
    linkedQuickBooks: str


async def getCustomerDetails(
    customerId: str,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> CustomerDetailsResponse:
    """
    Retrieves detailed customer information including customer preferences, order history, and linked QuickBooks billing info. Expected to return customer data if found, or an appropriate error message if not found. Useful for all front-facing teams providing personalized customer services.

    Args:
        customerId (str): Unique identifier for the customer whose details are being retrieved.
        current_user (prisma.models.User): The currently authenticated user, automatically injected by FastAPI's dependency injection.

    Returns:
        CustomerDetailsResponse: Outputs detailed information about a customer, such as their preferences, order history, and associated QuickBooks billing info.
    """
    customer = await prisma.models.Customer.prisma().find_unique(
        where={"id": int(customerId)},
        include={"orders": {"include": {"items": {"include": {"item": True}}}}},
    )
    if customer is None:
        raise ValueError("Customer not found")
    orders = []
    for order in customer.orders:
        items = [
            OrderItemData(
                itemId=item.itemId, name=item.item.name, quantity=item.quantity
            )
            for item in order.items
        ]
        orders.append(
            OrderData(
                orderId=order.id,
                status=OrderStatus(status=order.status),
                placedAt=order.placedAt,
                items=items,
            )
        )
    linked_quickbooks = "Link or Data for QuickBooks associated with Customer ID"
    return CustomerDetailsResponse(
        firstName=customer.firstName,
        lastName=customer.lastName,
        email=customer.email,
        phone=customer.phone,
        preferences=customer.preferences,
        orders=orders,
        linkedQuickBooks=linked_quickbooks,
    )
