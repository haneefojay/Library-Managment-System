from fastapi import FastAPI
from .models import Base
from .database import engine
from .routers import auth, user, book, borrow_book, authors

app = FastAPI(title="Library Management API", version="0.1.0")

@app.get("/")
async def root():
    return{"meessage": "Hello World!"}

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(book.router)
app.include_router(borrow_book.router)
app.include_router(authors.router)