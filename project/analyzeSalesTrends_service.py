from collections import Counter
from typing import Annotated, Dict, List, Optional

import prisma
import prisma.enums
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class SalesTrendsResponse(BaseModel):
    """
    Provides detailed insights into sales trends over the specified period and segmented further if necessary. Includes peak periods, top products, and trends in customer buying behavior.
    """

    peak_periods: List[str]
    top_products: List[str]
    customer_trends: Dict[str, Dict]


async def get_current_active_user():
    """
    Retrieves the current active and authenticated user. This is a dummy implementation to satisfy function signature.

    Returns:
        prisma.models.User: The retrieved user if present and active, otherwise returns None.
    """
    users = await prisma.models.User.prisma().find_many(where={"disabled": False})
    return users[0] if users else None


async def analyzeSalesTrends(
    start_date: str,
    end_date: str,
    product: Optional[str],
    customer_segment: Optional[str],
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> SalesTrendsResponse:
    """
    Analyzes sales trends and provides insights, such as peak selling periods and high-demand products.
    This data feeds into the Reporting and Analytics Module for detailed financial reporting and trend prediction.

    Args:
        start_date (str): The beginning of the date range for which sales data should be analyzed.
        end_date (str): The end of the date range for which sales data should be analyzed.
        product (Optional[str]): Optional filter to analyze trends for a specific product.
        customer_segment (Optional[str]): Optional filter to segment the sales data by types of customers.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): User performing the operation, using it to apply user-specific filters or permissions.

    Returns:
        SalesTrendsResponse: Provides detailed insights into sales trends over the specified period and segmented further if necessary.
    """
    if current_user is None or current_user.role not in [
        prisma.enums.Role.SalesManager,
        prisma.enums.Role.AnalyticsManager,
    ]:  # TODO(autogpt): Cannot access member "AnalyticsManager" for type "type[Role]"
        #     Member "AnalyticsManager" is unknown. reportAttributeAccessIssue
        raise PermissionError("Access denied: user is not authorized or not active.")
    filters = {"placedAt": {"gte": start_date, "lte": end_date}}
    if product:
        filters["items"] = {"some": {"item": {"name": product}}}
    if customer_segment:
        filters["customer"] = {"segment": customer_segment}
    orders = await prisma.models.Order.prisma().find_many(
        where=filters, include={"items": {"include": {"item": True}}, "customer": True}
    )
    peak_periods = []
    top_products_count = {}
    customers_trend = {}
    for order in orders:
        month = order.placedAt.strftime("%Y-%m")
        peak_periods.append(month)
        for item in order.items:
            product_name = item.item.name
            if product_name not in top_products_count:
                top_products_count[product_name] = 0
            top_products_count[product_name] += item.quantity
        customer_id = order.customer.id
        if customer_id not in customers_trend:
            customers_trend[customer_id] = {"count": 0, "segments": set()}
        customers_trend[customer_id]["count"] += 1
        customers_trend[customer_id]["segments"].add(customer_segment)
    peak_periods_count = Counter(peak_periods)
    top_peak_periods = [
        period
        for period, count in peak_periods_count.items()
        if count == max(peak_periods_count.values())
    ]
    sorted_top_products = sorted(
        top_products_count.items(), key=lambda kv: kv[1], reverse=True
    )[:5]
    top_products = [product for product, count in sorted_top_products]
    formatted_customer_trends = {
        cust_id: {"order_count": data["count"], "segments": list(data["segments"])}
        for cust_id, data in customers_trend.items()
    }
    return SalesTrendsResponse(
        peak_periods=top_peak_periods,
        top_products=top_products,
        customer_trends=formatted_customer_trends,
    )
