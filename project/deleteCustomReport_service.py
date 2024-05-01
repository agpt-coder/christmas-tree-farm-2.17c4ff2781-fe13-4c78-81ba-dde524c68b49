from typing import Annotated

import prisma
import prisma.models
from fastapi import Depends, HTTPException
from pydantic import BaseModel


def get_current_active_user():  # type: ignore
    """
    A dependency that extracts and returns the current active user from the request.
    This is a placeholder for the real authentication handling logic.
    """
    pass


class DeleteReportResponse(BaseModel):
    """
    Response model indicating the result of the delete operation for a custom report. Includes success or error messages.
    """

    success: bool
    message: str


async def deleteCustomReport(
    reportId: str,
    role: str,
    current_user: Annotated[prisma.models.User, Depends(get_current_active_user)],
) -> DeleteReportResponse:
    """
    Provides functionality for deleting a previously generated custom report. This endpoint ensures that only authorized roles can remove reports, maintaining data integrity and compliance with data management policies. The user must provide the unique report ID as a path parameter, and the system will validate permissions before proceeding with deletion.

    Args:
        reportId (str): Unique identifier for the custom report to be deleted.
        role (str): Role of the user making the request. This is used to ensure the user is allowed to delete reports.
        current_user (Annotated[prisma.models.User, Depends(get_current_active_user)]): The current authenticated user.

    Returns:
        DeleteReportResponse: Response model indicating the result of the delete operation for a custom report. Includes success or error messages.

    Raises:
        HTTPException: 403 if the user role is not authorized to delete reports.
        HTTPException: 404 if no report exists with the provided ID.
    """
    if role.lower() not in ["admin", "reportinganalyst"]:
        raise HTTPException(
            status_code=403, detail="You do not have the permission to delete reports."
        )
    report = await prisma.models.InventoryItem.prisma().find_unique(
        where={"id": int(reportId)}
    )
    if report is None:
        raise HTTPException(
            status_code=404, detail=f"Report with ID '{reportId}' not found."
        )
    await prisma.models.InventoryItem.prisma().delete(where={"id": int(reportId)})
    return DeleteReportResponse(success=True, message="Report deleted successfully.")
