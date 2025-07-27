from fastapi import Depends, HTTPException, status, Request
from jose import jwt
import requests
import os
from typing import Optional

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_PROJECT_ID = os.getenv("SUPABASE_PROJECT_ID")

def get_current_user(request: Request) -> str:
    """
    Verify Supabase JWT token and return user ID
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience=SUPABASE_PROJECT_ID
        )
        
        # Extract user ID from the token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        ) 