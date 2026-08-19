from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
REALM = os.getenv("REALM_NAME")
EXPECTED_AUDIENCE = os.getenv("EXPECTED_AUDIENCE")

ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{ISSUER}/protocol/openid-connect/auth",
    tokenUrl=f"{ISSUER}/protocol/openid-connect/token",
    auto_error=False,
)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    oauth2_token: str = Depends(oauth2_scheme),
    bearer_creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = oauth2_token or (bearer_creds.credentials if bearer_creds else None)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get Keycloak public keys
    async with httpx.AsyncClient() as client:
        response = await client.get(JWKS_URL)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve Keycloak public keys",
        )

    jwks = response.json()

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        key = next(
            key for key in jwks["keys"]
            if key["kid"] == kid
        )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=EXPECTED_AUDIENCE,
        )
        print(payload)

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except StopIteration:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signing key",
            headers={"WWW-Authenticate": "Bearer"},
        )