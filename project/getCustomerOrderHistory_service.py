from datetime import datetime
from typing import Annotated, List

import prisma
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class OrderStatus(BaseModel):
    """
    Describes the status of an order, can be one of several pre-defined states like 'Pending', 'Shipped', etc.
    """

    status: str


class OrderItemDetails(BaseModel):
    """
    Details of individual items in an order.
    """

    itemName: str
    quantity: int
    price: float


class CustomerOrder(BaseModel):
    """
    Represents a detailed customer order including items involved.
    """

    orderId: int
    placedAt: datetime
    status: OrderStatus
    items: List[OrderItemDetails]


class CustomerOrderHistoryResponse(BaseModel):
    """
    The ensemble response structure for a customer's order history, including all past orders with their contents, status, and dates. This includes a list of orders, with each order containing detailed list of items and their respective details.
    """

    orders: List[CustomerOrder]


async def getCustomerOrderHistory(
    customerId: int, current_user: Annotated[prisma.models.User, Depends]
) -> CustomerOrderHistoryResponse:
    """
    Fetches order history for a specific customer, interfacing with the Order Management Module to pull data tailored to customer queries. Provides an extensive list of past orders, each with detailed order contents, statuses, and dates.

    Args:
        customerId (int): The unique identifier for a customer to fetch order history.
        current_user (Annotated[prisma.models.User, Depends]): The common dependency used to authenticate and authorize the current active user.

    Returns:
        CustomerOrderHistoryResponse: The ensemble response structure for a customer's order history, including all past orders with their contents, status, and dates. This includes a list of orders, with each order containing detailed list of items and their respective details.
    """
    orders_data = await prisma.models.Order.prisma().find_many(
        where={"customerId": customerId}, include={"items": {"include": {"item": True}}}
    )
    response_orders = []
    for order in orders_data:
        order_items = []
        for item in order.items:
            if item.item:
                order_item = OrderItemDetails(
                    itemName=item.item.name,
                    quantity=item.quantity,
                    price=item.item.price,
                )  # TODO(autogpt): Cannot access member "price" for type "InventoryItem"
                #     Member "price" is unknown. reportAttributeAccessIssue
                order_items.append(order_item)
        order_status = OrderStatus(
            status=order.status.name if order.status else "Unknown"
        )
        customer_order = CustomerOrder(
            orderId=order.id,
            placedAt=order.placedAt,
            status=order_status,
            items=order_items,
        )
        response_orders.append(customer_order)
    return CustomerOrderHistoryResponse(orders=response_orders)
