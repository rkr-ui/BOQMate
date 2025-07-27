from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from security import security_manager

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = security_manager.get_client_ip(request)
        
        # Check if IP is blocked
        if security_manager.is_ip_blocked(client_ip):
            security_manager.log_security_event("BLOCKED_IP_ACCESS", {
                "ip": client_ip,
                "path": request.url.path,
                "method": request.method
            })
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Rate limiting
        if not security_manager.check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Security headers
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:;"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Validate request body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Check for suspicious content in body
                    body_str = body.decode('utf-8', errors='ignore')
                    if not security_manager.validate_input(body_str):
                        security_manager.log_security_event("MALICIOUS_INPUT", {
                            "ip": security_manager.get_client_ip(request),
                            "path": request.url.path,
                            "method": request.method,
                            "body_preview": body_str[:100]
                        })
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid input detected"}
                        )
            except Exception as e:
                logger.error(f"Error validating request body: {e}")
        
        # Validate query parameters
        for param_name, param_value in request.query_params.items():
            if not security_manager.validate_input(param_value):
                security_manager.log_security_event("MALICIOUS_QUERY_PARAM", {
                    "ip": security_manager.get_client_ip(request),
                    "path": request.url.path,
                    "param": param_name,
                    "value": param_value
                })
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid query parameter"}
                )
        
        response = await call_next(request)
        return response

class FileUploadSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if this is a file upload endpoint
        if request.url.path == "/api/generate-boq" and request.method == "POST":
            try:
                # Get form data
                form = await request.form()
                
                # Validate file
                if "file" in form:
                    file = form["file"]
                    filename = file.filename
                    
                    # Sanitize filename
                    if filename:
                        sanitized_filename = security_manager.sanitize_filename(filename)
                        if sanitized_filename != filename:
                            security_manager.log_security_event("SUSPICIOUS_FILENAME", {
                                "ip": security_manager.get_client_ip(request),
                                "original_filename": filename,
                                "sanitized_filename": sanitized_filename
                            })
                    
                    # Validate file type
                    allowed_extensions = ['pdf', 'txt', 'docx', 'dwg', 'dxf', 'rvt', 'rfa', 'dgn', 'skp']
                    if not security_manager.validate_file_type(filename, allowed_extensions):
                        security_manager.log_security_event("INVALID_FILE_TYPE", {
                            "ip": security_manager.get_client_ip(request),
                            "filename": filename
                        })
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid file type"}
                        )
                    
                    # Check file size (limit to 50MB)
                    file_content = await file.read()
                    if len(file_content) > 50 * 1024 * 1024:  # 50MB
                        security_manager.log_security_event("FILE_TOO_LARGE", {
                            "ip": security_manager.get_client_ip(request),
                            "filename": filename,
                            "size": len(file_content)
                        })
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={"detail": "File too large"}
                        )
                    
                    # Validate file content for malicious patterns
                    file_content_str = file_content.decode('utf-8', errors='ignore')
                    if not security_manager.validate_input(file_content_str):
                        security_manager.log_security_event("MALICIOUS_FILE_CONTENT", {
                            "ip": security_manager.get_client_ip(request),
                            "filename": filename
                        })
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "File content validation failed"}
                        )
                
                # Validate categories parameter if present
                if "categories" in form:
                    categories = form["categories"]
                    if not security_manager.validate_input(categories):
                        security_manager.log_security_event("MALICIOUS_CATEGORIES", {
                            "ip": security_manager.get_client_ip(request),
                            "categories": categories
                        })
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid categories parameter"}
                        )
                        
            except Exception as e:
                logger.error(f"Error in file upload security check: {e}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "File upload validation failed"}
                )
        
        response = await call_next(request)
        return response

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        public_paths = ["/", "/health", "/api/categories"]
        
        if request.url.path in public_paths:
            response = await call_next(request)
            return response
        
        # Check for authentication header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            security_manager.log_security_event("MISSING_AUTH", {
                "ip": security_manager.get_client_ip(request),
                "path": request.url.path
            })
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"}
            )
        
        # Validate token
        token = auth_header.split(" ")[1]
        payload = security_manager.verify_token(token)
        
        if not payload:
            security_manager.log_security_event("INVALID_TOKEN", {
                "ip": security_manager.get_client_ip(request),
                "path": request.url.path
            })
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Add user info to request state
        request.state.user_id = payload.get("user_id")
        
        response = await call_next(request)
        return response