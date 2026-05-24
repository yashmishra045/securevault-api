import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('securevault')


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.config import settings
    from app.database import get_engine, Base
    logger.info('Starting SecureVault API...')
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info('Database ready!')
    yield
    await engine.dispose()
    logger.info('Shutdown complete.')


app = FastAPI(title='SecureVault API', version='1.0.0', lifespan=lifespan)


@asynccontextmanager
async def _get_settings():
    from app.config import settings
    return settings


from app.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

from app.middleware.rate_limiter import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware, rate_limit=100, window_seconds=60)


@app.middleware('http')
async def request_logger(request: Request, call_next) -> Response:
    req_id = str(uuid.uuid4())[:8]
    request.state.request_id = req_id
    start = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers['X-Request-ID'] = req_id
    logger.info(f'{request.method} {request.url.path} -> {response.status_code} ({ms}ms)')
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc):
    return JSONResponse(status_code=exc.status_code, content={'error': {'code': exc.status_code, 'message': exc.detail}})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc):
    return JSONResponse(status_code=422, content={'error': {'code': 422, 'message': 'Validation failed'}})


from app.routers import auth, secrets, admin, audit, health

app.include_router(health.router, prefix='/health', tags=['Health'])
app.include_router(auth.router, prefix='/auth', tags=['Auth'])
app.include_router(secrets.router, prefix='/secrets', tags=['Secrets'])
app.include_router(admin.router, prefix='/admin', tags=['Admin'])
app.include_router(audit.router, prefix='/audit', tags=['Audit'])


@app.get('/')
async def root():
    return {'service': 'SecureVault API', 'version': '1.0.0', 'docs': '/docs'}