from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.files import router
from middleware.security_middleware import (
    SecurityMiddleware, 
    InputValidationMiddleware, 
    FileUploadSecurityMiddleware, 
    AuthenticationMiddleware
)

app = FastAPI(title="BOQMate API", version="1.0.0")

# Add security middleware (order matters!)
app.add_middleware(SecurityMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(FileUploadSecurityMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "BOQMate API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 