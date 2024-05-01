from typing import Annotated

import prisma
import prisma.models
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


class CreateInventoryItemResponse(BaseModel):
    """
    Response model representing the newly created inventory item.
    """

    id: int
    name: str
    category: str
    quantity: int
    threshold: int
    unit: str


get_current_active_user = OAuth2PasswordBearer(tokenUrl="token")


async def createInventoryItem(
    name: str,
    category: str,
    initial_quantity: int,
    supplier: str,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> CreateInventoryItemResponse:
    """
    Allows the creation of a new inventory item. Users must provide relevant item details such as name, category, initial quantity, and supplier. Ensures new stock is logged and traceable from the point of entry.

    Args:
        name (str): Name of the inventory item to be created.
        category (str): Category of the inventory item such as 'Tree', 'Fertilizer', 'Equipment', etc.
        initial_quantity (int): Initial quantity count for the new inventory item.
        supplier (str): Name or ID of the supplier for the item.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The current authenticated user performing the operation.

    Returns:
        CreateInventoryItemResponse: Response model representing the newly created inventory item.

    The function performs the following steps:
    - Creates a new 'InventoryItem' record with the provided details.
    - Inserts a new 'InventoryLog' record to record the addition of stock.
    - Constructs and returns a 'CreateInventoryItemResponse' with the item details.
    """
    new_item = await prisma.models.InventoryItem.prisma().create(
        data={
            "name": name,
            "type": category,
            "quantity": initial_quantity,
            "threshold": 10,
            "unit": "units",
        }
    )
    await prisma.models.InventoryLog.prisma().create(
        data={
            "itemId": new_item.id,
            "changedBy": current_user.id,
            "changeType": "Received",
            "amount": initial_quantity,
        }
    )
    return CreateInventoryItemResponse(
        id=new_item.id,
        name=new_item.name,
        category=new_item.type,
        quantity=new_item.quantity,
        threshold=new_item.threshold,
        unit=new_item.unit,
    )
