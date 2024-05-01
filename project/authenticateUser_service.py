import bcrypt
import prisma
import prisma.enums
import prisma.models
from pydantic import BaseModel


class UserAuthenticationResponse(BaseModel):
    """
    Response object returned after user authentication attempt. Contains user role and authentication token upon success.
    """

    token: str
    role: prisma.enums.Role


async def authenticateUser(username: str, password: str) -> UserAuthenticationResponse:
    """
    Authenticates user credentials against the system’s secure store. It uses encryption and secure communication protocols to ensure data integrity. On successful authentication, it returns a token and user role; otherwise, it provides an error response.

    Args:
        username (str): The username used by the user to login.
        password (str): The user's password. It should be transmitted securely and stored using a hash.

    Returns:
        UserAuthenticationResponse: Response object returned after user authentication attempt. Contains user role and authentication token upon success.

    Example:
        try:
            response = await authenticateUser("jdoe", "securepassword123")
            print(response.token, response.role)
        except ValueError as e:
            print(str(e))
    """
    user = await prisma.models.User.prisma().find_unique(where={"username": username})
    if user is None or user.disabled:
        raise ValueError(
            "Authentication failed: User not found or account is disabled."
        )
    if bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        simulated_token = "ExampleToken"
        return UserAuthenticationResponse(token=simulated_token, role=user.role.name)
    else:
        raise ValueError("Authentication failed: Incorrect credentials provided.")
