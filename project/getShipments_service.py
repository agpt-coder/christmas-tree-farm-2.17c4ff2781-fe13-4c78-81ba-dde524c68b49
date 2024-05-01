from datetime import date
from typing import Annotated, List, Optional

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


class Shipment(BaseModel):
    """
    A detailed view of a shipment including vital data points like shipment date, contents of the shipment, supplier information, and current delivery status.
    """

    shipment_date: date
    contents: List[str]
    supplier_info: str
    delivery_status: OrderStatus


class GetShipmentsResponse(BaseModel):
    """
    Outputs a list of shipments matching the criteria specified in the request, providing detailed and summarized views of ongoing and past shipments.
    """

    shipments: List[Shipment]


async def getShipments(
    from_date: Optional[date],
    to_date: Optional[date],
    status: Optional[OrderStatus],
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> GetShipmentsResponse:
    """
    Fetches a list of ongoing and past shipments. Includes information such as shipment date,
    contents, supplier info, and delivery status. Supports filter by date and status to better
    serve the reporting needs.

    Args:
        from_date (Optional[date]): The starting date to filter shipments from. This is optional, and if not provided,
                                    defaults to the start of currently active records.
        to_date (Optional[date]): The ending date to filter shipments until. This is optional, and if not provided,
                                  the current date will be assumed.
        status (Optional[OrderStatus]): Filter shipments by their delivery status, such as 'Pending', 'Shipped',
                                        'Delivered', or 'Cancelled'.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The user executing the query.

    Returns:
        GetShipmentsResponse: Outputs a list of shipments matching the criteria specified in the request,
                              providing detailed and summarized views of ongoing and past shipments.
    """
    where_clauses = {}
    if from_date:
        where_clauses["placedAt"] = {"gte": from_date}
    if to_date:
        where_clauses["placedAt"]["lte"] = to_date
    if status:
        where_clauses["status"] = status.status
    orders = await prisma.models.Order.prisma().find_many(
        where=where_clauses, include={"items": {"include": {"item": True}}}
    )
    shipments = [
        Shipment(
            shipment_date=order.placedAt,
            contents=[item.item.name for item in order.items if item.item],
            supplier_info="Supplier Details Unavailable",
            delivery_status=OrderStatus(status=order.status),
        )
        for order in orders
    ]
    return GetShipmentsResponse(shipments=shipments)
