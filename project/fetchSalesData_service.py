from datetime import date, datetime
from typing import Annotated, List, Optional

import prisma
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class SaleRecord(BaseModel):
    """
    Detailed individual sales record.
    """

    productId: int
    quantity: int
    price: float
    saleDate: datetime


class SalesDataResponse(BaseModel):
    """
    Response model for the sales data. Contains detailed listings of all sales transactions based on the provided filters.
    """

    salesRecords: List[SaleRecord]


async def get_current_active_user():
    """
    A stub function to fetch the currently active user. In practice, this would extract user details from a security token or session.
    """
    return prisma.models.User(
        id=1,
        username="user",
        role="SalesManager",
        hashed_password="hashed",
        disabled=False,
    )


async def fetchSalesData(
    startDate: date,
    endDate: date,
    productId: Optional[int],
    productType: Optional[str],
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> SalesDataResponse:
    """
    Retrieves all sales data, including details such as product ID, quantity, price, and date. This endpoint will also
    handle filtering based on parameters like date ranges and product types, expected to interact with the Inventory
    Module to validate product IDs.

    Args:
        startDate (date): The start date for the sales data query.
        endDate (date): The end date for the sales data query.
        productId (Optional[int]): The product ID to filter the sales data. This parameter is optional and is validated
        against the InventoryItem database model to ensure it refers to a valid product.
        productType (Optional[str]): The type of product to filter the sales data, such as 'sapling', 'fertilizer', etc.
        This is optional and will match the 'type' field in the InventoryItem model.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The commons object used to
        add the user_id, check dependencies, and validate roles

    Returns:
        SalesDataResponse: Response model for the sales data. Contains detailed listings of all sales transactions based
        on the provided filters.
    """
    if current_user.role not in ["SalesManager", "Admin"]:
        raise PermissionError(
            "You do not have the necessary permissions to access sales data."
        )
    filters = {}
    if productId:
        filters["itemId"] = productId
    if productType:
        type_specific_items = await prisma.models.InventoryItem.prisma().find_many(
            where={"type": productType}
        )
        filters["itemId"] = {"in": [item.id for item in type_specific_items]}
    matching_orders = await prisma.models.OrderItem.prisma().find_many(
        where={"order": {"placedAt": {"gte": startDate, "lte": endDate}}, **filters},
        include={"item": True, "order": True},
    )
    sales_records = [
        SaleRecord(
            productId=order_item.item.id,
            quantity=order_item.quantity,
            price=float(order_item.item.unit),
            saleDate=order_item.order.placedAt,
        )
        for order_item in matching_orders
    ]
    return SalesDataResponse(salesRecords=sales_records)
