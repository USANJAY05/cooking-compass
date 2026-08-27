# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2AuthorizationCodeBearer, HTTPBearer, HTTPAuthorizationCredentials
# from jose import jwt, JWTError
# import httpx
# from dotenv import load_dotenv
# import os

# load_dotenv()

# KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
# REALM = os.getenv("REALM_NAME")
# EXPECTED_AUDIENCE = os.getenv("EXPECTED_AUDIENCE")

# ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
# JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# oauth2_scheme = OAuth2AuthorizationCodeBearer(
#     authorizationUrl=f"{ISSUER}/protocol/openid-connect/auth",
#     tokenUrl=f"{ISSUER}/protocol/openid-connect/token",
#     auto_error=False,
# )
# bearer_scheme = HTTPBearer(auto_error=False)


# async def get_current_user(
#     oauth2_token: str = Depends(oauth2_scheme),
#     bearer_creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
# ):
#     token = oauth2_token or (bearer_creds.credentials if bearer_creds else None)

#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     # Get Keycloak public keys
#     async with httpx.AsyncClient() as client:
#         response = await client.get(JWKS_URL)

#     if response.status_code != 200:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Unable to retrieve Keycloak public keys",
#         )

#     jwks = response.json()

#     try:
#         unverified_header = jwt.get_unverified_header(token)
#         kid = unverified_header.get("kid")

#         key = next(
#             key for key in jwks["keys"]
#             if key["kid"] == kid
#         )

#         payload = jwt.decode(
#             token,
#             key,
#             algorithms=["RS256"],
#             issuer=ISSUER,
#             audience=EXPECTED_AUDIENCE,
#         )
#         print(payload)

#         return payload

#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except StopIteration:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token signing key",
#             headers={"WWW-Authenticate": "Bearer"},
#         )








# from fastapi import Depends, HTTPException, status
# from fastapi.security import (
#     OAuth2AuthorizationCodeBearer,
#     HTTPBearer,
#     HTTPAuthorizationCredentials,
# )
# from jose import jwt, JWTError
# import httpx
# from dotenv import load_dotenv
# import os


# load_dotenv()


# # ============================================================
# # Configuration
# # ============================================================

# KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
# REALM = os.getenv("REALM_NAME")
# EXPECTED_AUDIENCE = os.getenv("EXPECTED_AUDIENCE")

# ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
# JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"


# print("========== Keycloak Configuration ==========")
# print(f"KEYCLOAK_URL      : {KEYCLOAK_URL}")
# print(f"REALM             : {REALM}")
# print(f"ISSUER            : {ISSUER}")
# print(f"JWKS_URL          : {JWKS_URL}")
# print(f"EXPECTED_AUDIENCE : {EXPECTED_AUDIENCE}")
# print("============================================")


# # ============================================================
# # Authentication schemes
# # ============================================================

# oauth2_scheme = OAuth2AuthorizationCodeBearer(
#     authorizationUrl=f"{ISSUER}/protocol/openid-connect/auth",
#     tokenUrl=f"{ISSUER}/protocol/openid-connect/token",
#     auto_error=False,
# )

# bearer_scheme = HTTPBearer(auto_error=False)


# # ============================================================
# # Current User
# # ============================================================

# async def get_current_user(
#     oauth2_token: str = Depends(oauth2_scheme),
#     bearer_creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
# ):
#     print("\n========== Authentication Request ==========")

#     # --------------------------------------------------------
#     # Get token
#     # --------------------------------------------------------

#     token = oauth2_token or (
#         bearer_creds.credentials if bearer_creds else None
#     )

#     if not token:
#         print("❌ No authentication token provided")

#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     print("✅ Authentication token received")
#     print(f"Token length: {len(token)}")


#     # --------------------------------------------------------
#     # Get Keycloak JWKS
#     # --------------------------------------------------------

#     print("\nFetching Keycloak public keys...")
#     print(f"JWKS URL: {JWKS_URL}")

#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 JWKS_URL,
#                 timeout=10.0,
#             )

#     except httpx.RequestError as e:
#         print("❌ Failed to connect to Keycloak")
#         print(f"Error type: {type(e).__name__}")
#         print(f"Error: {e}")

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Unable to connect to Keycloak",
#         )


#     if response.status_code != 200:
#         print("❌ Failed to retrieve Keycloak public keys")
#         print(f"Status code: {response.status_code}")
#         print(f"Response: {response.text}")

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Unable to retrieve Keycloak public keys",
#         )


#     jwks = response.json()

#     print("✅ Keycloak public keys retrieved")
#     print(f"Number of keys: {len(jwks.get('keys', []))}")


#     # --------------------------------------------------------
#     # Read JWT header
#     # --------------------------------------------------------

#     try:
#         unverified_header = jwt.get_unverified_header(token)

#         print("\n========== JWT Header ==========")
#         print(unverified_header)

#         kid = unverified_header.get("kid")

#         print(f"Token kid: {kid}")

#         if not kid:
#             print("❌ JWT does not contain a kid")

#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token: missing kid",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )


#         # ----------------------------------------------------
#         # Find matching Keycloak public key
#         # ----------------------------------------------------

#         print("\nSearching for matching Keycloak public key...")

#         key = next(
#             key
#             for key in jwks["keys"]
#             if key.get("kid") == kid
#         )

#         print("✅ Matching public key found")
#         print(f"Key ID: {key.get('kid')}")
#         print(f"Key type: {key.get('kty')}")
#         print(f"Algorithm: {key.get('alg')}")


#         # ----------------------------------------------------
#         # Inspect unverified claims
#         # ----------------------------------------------------

#         unverified_payload = jwt.get_unverified_claims(token)

#         print("\n========== JWT Claims (Unverified) ==========")

#         print(f"Subject (sub) : {unverified_payload.get('sub')}")
#         print(f"Issuer (iss)  : {unverified_payload.get('iss')}")
#         print(f"Audience (aud): {unverified_payload.get('aud')}")
#         print(f"Expiration    : {unverified_payload.get('exp')}")
#         print(f"Issued At     : {unverified_payload.get('iat')}")
#         print(f"Token Type    : {unverified_payload.get('typ')}")


#         # ----------------------------------------------------
#         # Compare expected values
#         # ----------------------------------------------------

#         print("\n========== JWT Validation Configuration ==========")

#         print(f"Expected issuer   : {ISSUER}")
#         print(f"Token issuer      : {unverified_payload.get('iss')}")

#         print(f"Expected audience : {EXPECTED_AUDIENCE}")
#         print(f"Token audience    : {unverified_payload.get('aud')}")


#         # ----------------------------------------------------
#         # Validate JWT
#         # ----------------------------------------------------

#         print("\nValidating JWT signature and claims...")

#         payload = jwt.decode(
#             token,
#             key,
#             algorithms=["RS256"],
#             issuer=ISSUER,
#             audience=EXPECTED_AUDIENCE,
#         )


#         # ----------------------------------------------------
#         # SUCCESS
#         # ----------------------------------------------------

#         print("\n✅ JWT VALIDATION SUCCESSFUL")

#         print("========== Verified JWT Payload ==========")
#         print(payload)
#         print("==========================================")

#         return payload


#     # --------------------------------------------------------
#     # No matching signing key
#     # --------------------------------------------------------

#     except StopIteration:

#         print("\n❌ JWT SIGNING KEY ERROR")

#         print(f"No public key found for kid: {kid}")

#         print("Available Keycloak kids:")

#         for key in jwks.get("keys", []):
#             print(f" - {key.get('kid')}")


#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token signing key",
#             headers={"WWW-Authenticate": "Bearer"},
#         )


#     # --------------------------------------------------------
#     # JWT validation error
#     # --------------------------------------------------------

#     except JWTError as e:

#         print("\n❌ JWT VALIDATION FAILED")

#         print(f"Error type: {type(e).__name__}")
#         print(f"Error     : {e}")

#         print("\nPossible validation values:")

#         try:
#             print(f"Expected issuer   : {ISSUER}")
#             print(f"Expected audience : {EXPECTED_AUDIENCE}")
#             print(f"Token issuer      : {unverified_payload.get('iss')}")
#             print(f"Token audience    : {unverified_payload.get('aud')}")
#         except Exception:
#             pass

#         print("============================================")


#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )


#     # --------------------------------------------------------
#     # Unexpected error
#     # --------------------------------------------------------

#     except Exception as e:

#         print("\n❌ UNEXPECTED AUTHENTICATION ERROR")

#         print(f"Error type: {type(e).__name__}")
#         print(f"Error     : {e}")

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Authentication error",
#         )




















from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2AuthorizationCodeBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from jose import jwt, JWTError
import httpx
from dotenv import load_dotenv
import os


load_dotenv()


# ============================================================
# Configuration
# ============================================================

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
REALM = os.getenv("REALM_NAME")
EXPECTED_AUDIENCE = os.getenv("EXPECTED_AUDIENCE")

# Keycloak client IDs
WEB_CLIENT_ID = os.getenv("KEYCLOAK_WEB_CLIENT_ID")
MOBILE_CLIENT_ID = os.getenv("KEYCLOAK_MOBILE_CLIENT_ID")

ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"


# Allowed clients
ALLOWED_CLIENTS = {
    WEB_CLIENT_ID: "web",
    MOBILE_CLIENT_ID: "mobile",
}


print("========== Keycloak Configuration ==========")
print(f"KEYCLOAK_URL       : {KEYCLOAK_URL}")
print(f"REALM              : {REALM}")
print(f"ISSUER             : {ISSUER}")
print(f"JWKS_URL           : {JWKS_URL}")
print(f"EXPECTED_AUDIENCE  : {EXPECTED_AUDIENCE}")
print(f"WEB_CLIENT_ID      : {WEB_CLIENT_ID}")
print(f"MOBILE_CLIENT_ID   : {MOBILE_CLIENT_ID}")
print("============================================")


# ============================================================
# Authentication schemes
# ============================================================

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{ISSUER}/protocol/openid-connect/auth",
    tokenUrl=f"{ISSUER}/protocol/openid-connect/token",
    auto_error=False,
)

bearer_scheme = HTTPBearer(auto_error=False)


# ============================================================
# Current User
# ============================================================

async def get_current_user(
    oauth2_token: str = Depends(oauth2_scheme),
    bearer_creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):

    print("\n========== Authentication Request ==========")

    # --------------------------------------------------------
    # Get token
    # --------------------------------------------------------

    token = oauth2_token or (
        bearer_creds.credentials if bearer_creds else None
    )

    if not token:
        print("❌ No authentication token provided")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print("✅ Authentication token received")
    print(f"Token length: {len(token)}")


    # --------------------------------------------------------
    # Get Keycloak JWKS
    # --------------------------------------------------------

    print("\nFetching Keycloak public keys...")
    print(f"JWKS URL: {JWKS_URL}")

    try:

        async with httpx.AsyncClient() as client:

            response = await client.get(
                JWKS_URL,
                timeout=10.0,
            )

    except httpx.RequestError as e:

        print("❌ Failed to connect to Keycloak")
        print(f"Error type: {type(e).__name__}")
        print(f"Error: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to connect to Keycloak",
        )


    if response.status_code != 200:

        print("❌ Failed to retrieve Keycloak public keys")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve Keycloak public keys",
        )


    jwks = response.json()

    print("✅ Keycloak public keys retrieved")
    print(
        f"Number of keys: {len(jwks.get('keys', []))}"
    )


    # --------------------------------------------------------
    # Read JWT header
    # --------------------------------------------------------

    try:

        unverified_header = jwt.get_unverified_header(token)

        print("\n========== JWT Header ==========")
        print(unverified_header)

        kid = unverified_header.get("kid")

        print(f"Token kid: {kid}")

        if not kid:

            print("❌ JWT does not contain a kid")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing kid",
                headers={"WWW-Authenticate": "Bearer"},
            )


        # ----------------------------------------------------
        # Find matching Keycloak public key
        # ----------------------------------------------------

        print("\nSearching for matching Keycloak public key...")

        key = next(
            key
            for key in jwks["keys"]
            if key.get("kid") == kid
        )

        print("✅ Matching public key found")
        print(f"Key ID: {key.get('kid')}")
        print(f"Key type: {key.get('kty')}")
        print(f"Algorithm: {key.get('alg')}")


        # ----------------------------------------------------
        # Inspect unverified claims
        # ----------------------------------------------------

        unverified_payload = jwt.get_unverified_claims(token)

        print("\n========== JWT Claims (Unverified) ==========")

        print(
            f"Subject (sub) : "
            f"{unverified_payload.get('sub')}"
        )

        print(
            f"Issuer (iss)  : "
            f"{unverified_payload.get('iss')}"
        )

        print(
            f"Audience (aud): "
            f"{unverified_payload.get('aud')}"
        )

        print(
            f"Authorized Party (azp): "
            f"{unverified_payload.get('azp')}"
        )

        print(
            f"Expiration    : "
            f"{unverified_payload.get('exp')}"
        )

        print(
            f"Issued At     : "
            f"{unverified_payload.get('iat')}"
        )

        print(
            f"Token Type    : "
            f"{unverified_payload.get('typ')}"
        )


        # ----------------------------------------------------
        # Validate issuer and audience
        # ----------------------------------------------------

        print("\n========== JWT Validation Configuration ==========")

        print(f"Expected issuer   : {ISSUER}")
        print(
            f"Token issuer      : "
            f"{unverified_payload.get('iss')}"
        )

        print(
            f"Expected audience : "
            f"{EXPECTED_AUDIENCE}"
        )

        print(
            f"Token audience    : "
            f"{unverified_payload.get('aud')}"
        )


        # ----------------------------------------------------
        # Validate JWT signature + issuer + audience
        # ----------------------------------------------------

        print("\nValidating JWT signature and claims...")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=EXPECTED_AUDIENCE,
        )


        # ----------------------------------------------------
        # Identify client
        # ----------------------------------------------------

        client_id = payload.get("azp")

        print("\n========== Client Identification ==========")
        print(f"Client ID: {client_id}")


        if not client_id:

            print("❌ Token does not contain azp")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing client identity",
                headers={"WWW-Authenticate": "Bearer"},
            )


        # ----------------------------------------------------
        # Validate client
        # ----------------------------------------------------

        client_type = ALLOWED_CLIENTS.get(client_id)

        if not client_type:

            print("❌ Unknown Keycloak client")
            print(f"Client ID: {client_id}")

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Client is not allowed",
            )


        print(f"Client type: {client_type}")


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print("\n✅ JWT VALIDATION SUCCESSFUL")

        print("========== Authentication Context ==========")

        print(
            f"User ID     : "
            f"{payload.get('sub')}"
        )

        print(
            f"Client ID   : "
            f"{client_id}"
        )

        print(
            f"Client Type : "
            f"{client_type}"
        )

        print(
            f"Audience    : "
            f"{payload.get('aud')}"
        )

        print("============================================")


        # ----------------------------------------------------
        # Add application-specific information
        # ----------------------------------------------------

        payload["client_id"] = client_id
        payload["client_type"] = client_type


        return payload


    # --------------------------------------------------------
    # No matching signing key
    # --------------------------------------------------------

    except StopIteration:

        print("\n❌ JWT SIGNING KEY ERROR")

        print(f"No public key found for kid: {kid}")

        print("Available Keycloak kids:")

        for key in jwks.get("keys", []):

            print(
                f" - {key.get('kid')}"
            )


        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signing key",
            headers={"WWW-Authenticate": "Bearer"},
        )


    # --------------------------------------------------------
    # JWT validation error
    # --------------------------------------------------------

    except JWTError as e:

        print("\n❌ JWT VALIDATION FAILED")

        print(f"Error type: {type(e).__name__}")
        print(f"Error: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


    # --------------------------------------------------------
    # Unexpected error
    # --------------------------------------------------------

    except HTTPException:
        raise


    except Exception as e:

        print("\n❌ UNEXPECTED AUTHENTICATION ERROR")

        print(f"Error type: {type(e).__name__}")
        print(f"Error: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )