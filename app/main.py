from fastapi import FastAPI
import asyncio
from .models import Base
from .database import engine, init_cache
from .routers import auth, register, book, borrow_book, notification, users, ws_notification
from .services.scheduler import scheduler_loop
from .core.limiter import limiter, rate_limit_handler


app = FastAPI(title="Library Management API", version="0.1.0")


app.state.limiter = limiter
app.add_exception_handler(429, rate_limit_handler)


@app.get("/")
async def root():
    return{"meessage": "Hello World!"}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))
    
    asyncio.create_task(scheduler_loop())
    
    await init_cache()

app.include_router(auth.router)
app.include_router(register.router)
app.include_router(book.router)
app.include_router(borrow_book.router)
app.include_router(users.router)
app.include_router(notification.router)
app.include_router(ws_notification.router)