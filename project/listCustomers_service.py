from datetime import date
from typing import Annotated, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


async def get_current_active_user():  # type: ignore
    """
    Fetches and returns the current active user by checking session or token validation.
    Must be replaced with actual authentication implementation in production.
    Note: This is a stub function for illustration.
    """
    pass


class CustomerData(BaseModel):
    """
    Essential details about a customer including name, ID, and recent order status for quick reference.
    """

    id: int
    first_name: str
    last_name: str
    email: str
    recent_order_status: Optional[prisma.enums.OrderStatus] = None
    last_order_date: Optional[date] = None


class CustomerOverview(BaseModel):
    """
    Represents a simplified customer data suitable for quick views and reports, enriching necessary fields for business operations.
    """

    customers: List[CustomerData]


async def listCustomers(
    status: Optional[prisma.enums.OrderStatus],
    last_order_date_from: Optional[date],
    last_order_date_to: Optional[date],
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> CustomerOverview:
    """
    Provides a list of all customers with essential details and supports filtering based on order status
    and order date range. Requires current active user context to access.

    Args:
        status (Optional[prisma.enums.OrderStatus]): Filter by the status of the customers' last orders.
        last_order_date_from (Optional[date]): Filter customers with last order on or after this date.
        last_order_date_to (Optional[date]): Filter customers with last order on or before this date.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The currently authenticated user.

    Returns:
        CustomerOverview: Contains a list of customer data, convenient for quick reviews and reports.
    """
    filters = {}
    if status:
        filters["orders"] = {"some": {"status": status}}
    if last_order_date_from or last_order_date_to:
        date_filter = {}
        if last_order_date_from:
            date_filter["gte"] = last_order_date_from
        if last_order_date_to:
            date_filter["lte"] = last_order_date_to
        filters.setdefault("orders", {"some": {}})["some"].setdefault(
            "placedAt", {}
        ).update(date_filter)
    customers = await prisma.models.Customer.prisma().find_many(
        include={"orders": True}, where=filters
    )
    customer_overview_list = [
        CustomerData(
            id=customer.id,
            first_name=customer.firstName,
            last_name=customer.lastName,
            email=customer.email,
            recent_order_status=customer.orders[-1].status if customer.orders else None,
            last_order_date=customer.orders[-1].placedAt if customer.orders else None,
        )
        for customer in customers
    ]
    return CustomerOverview(customers=customer_overview_list)
