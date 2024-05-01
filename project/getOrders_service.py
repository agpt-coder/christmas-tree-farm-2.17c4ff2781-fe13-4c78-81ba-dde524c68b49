from datetime import datetime
from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends, HTTPException
from pydantic import BaseModel


class CustomerBrief(BaseModel):
    """
    Condensed customer information relevant to an order.
    """

    id: int
    fullName: str
    email: str


class ItemDetail(BaseModel):
    """
    Details of each item ordered, including pricing and quantity.
    """

    name: str
    quantity: int
    price: float


class OrderExpanded(BaseModel):
    """
    Detailed schema of an order which includes customer and item specifics.
    """

    id: int
    customer: CustomerBrief
    items: List[ItemDetail]
    totalPrice: float
    status: prisma.enums.OrderStatus
    placedAt: datetime


class OrdersResponse(BaseModel):
    """
    This model provides a structured list of orders, each detailing the customer information, items ordered, their quantities, pricing, and the order status.
    """

    orders: List[OrderExpanded]


async def get_current_active_user() -> prisma.models.User:
    """
    Retrieves the current active user. Assumes a function that checks if the user is not disabled and is properly authenticated.

    Returns:
        prisma.models.User: Authenticated user details.

    Raises:
        HTTPException: If the user is disabled or authentication fails.
    """
    user = await prisma.models.User.prisma().find_first(where={"disabled": False})
    if not user:
        raise HTTPException(status_code=404, detail="User not found or disabled.")
    return user


async def getOrders(
    customer_id: Optional[int] = None,
    status: Optional[prisma.enums.OrderStatus] = None,
    page: Optional[int] = 1,
    limit: Optional[int] = 10,
    sort_by: Optional[str] = "placedAt",
    sort_order: Optional[str] = "asc",
    current_user: Annotated[
        prisma.models.User, Depends(get_current_active_user)
    ] = Depends(get_current_active_user),
) -> OrdersResponse:
    """
    Retrieves and returns detailed orders from the database with various optional filters and pagination.
    It integrates customer and inventory item details into the response.

    Args:
        customer_id (Optional[int]): Filter to fetch orders for a specific customer.
        status (Optional[prisma.enums.OrderStatus]): Filter to fetch orders matching specific status.
        page (Optional[int]): Page number for pagination (1-indexed).
        limit (Optional[int]): Number of orders to return per page.
        sort_by (Optional[str]): Attribute name to sort by.
        sort_order (Optional[str]): Direction of sorting, 'asc' or 'desc'.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): Ensures that an authenticated user makes the request.

    Returns:
        OrdersResponse: A structured response containing a list of detailed orders.

    Raises:
        HTTPException: For access issues or incorrect query usage.
    """
    skip_amount = (page - 1) * limit
    where_conditions = {}
    if customer_id is not None:
        where_conditions["customer_id"] = customer_id
    if status is not None:
        where_conditions["status"] = status
    sort_conditions = {sort_by: sort_order} if sort_by and sort_order else {}
    orders_query = await prisma.models.Order.prisma().find_many(
        skip=skip_amount,
        take=limit,
        where=where_conditions,
        order=sort_conditions,
        include={"customer": True, "items": {"include": {"item": True}}},
    )
    orders_responses = []
    for order in orders_query:
        items_details = [
            ItemDetail(
                name=item_detail.item.name,
                quantity=item_detail.quantity,
                price=float(item_detail.item.unit_price),
            )
            for item_detail in order.items
        ]  # TODO(autogpt): Cannot access member "unit_price" for type "InventoryItem"
        #     Member "unit_price" is unknown. reportAttributeAccessIssue
        total_price = sum((item.price * item.quantity for item in items_details))
        orders_responses.append(
            OrderExpanded(
                id=order.id,
                customer=CustomerBrief(
                    id=order.customer.id,
                    fullName=f"{order.customer.firstName} {order.customer.lastName}",
                    email=order.customer.email,
                ),
                items=items_details,
                totalPrice=total_price,
                status=order.status,
                placedAt=order.placedAt,
            )
        )
    return OrdersResponse(orders=orders_responses)
