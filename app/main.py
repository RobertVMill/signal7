import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from .api.v1 import research
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)}
        )

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    logger.info("Successfully mounted static files")
except Exception as e:
    logger.error(f"Failed to mount static files: {str(e)}", exc_info=True)

# Include routers
app.include_router(research.router, prefix="/api/v1")

@app.get("/")
async def read_root():
    try:
        logger.info("Serving root page")
        return FileResponse('app/static/index.html')
    except Exception as e:
        logger.error(f"Failed to serve root page: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pages/{page_name}")
async def serve_pages(page_name: str):
    try:
        logger.info(f"Serving page: {page_name}")
        return FileResponse(f'app/static/pages/{page_name}/index.html')
    except Exception as e:
        logger.error(f"Failed to serve page {page_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
