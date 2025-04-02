import uvicorn
from fastapi import FastAPI
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse
import asyncio
from datetime import time, datetime, timedelta
import database

import schemas
import handlers


app = FastAPI()


async def scheduled_cleanup():
    while True:
        current_time = datetime.now()
        next_execution = datetime.combine(current_time.date(), time(3, 0))
        if current_time > next_execution:
            next_execution += timedelta(days=1)

        await asyncio.sleep((next_execution - current_time).total_seconds())

        async with database.get_db() as db:
            await handlers.purge_old_links(db)
            redis_conn = await database.get_redis().__anext__()
            await handlers.cache_popular_links(db, redis_conn)

            await redis_conn.delete(*await redis_conn.keys("stats:*"))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduled_cleanup())


@app.post("/links/shorten")
async def shorted_link(link: schemas.LinkCreate, db: AsyncSession = Depends(database.get_db)):
    return await handlers.create_link(db, link)

@app.get("/links/{short_code}")
async def redirect_to_original(short_code: str, db: AsyncSession = Depends(database.get_db)):
    full_link = await handlers.get_link_by_short_code(db, short_code)
    await handlers.increment_link_clicks(db, full_link )
    return RedirectResponse(url = full_link.original_url)


@app.delete("/links/{short_code}")
async def delete_short_score(short_code: str, db: AsyncSession = Depends(database.get_db)):
    await handlers.get_link_deleted(db,short_code)
    return {"message" : f"Link has {short_code} has been deleted"}

@app.put("/links/{short_code}")
async def update_link_by_short(short_code: str, new_url: schemas.LinkCreate, db: AsyncSession = Depends(database.get_db)):
    await handlers.update_link(db, short_code, new_url)
    return {"message":"Link has been changed"}

@app.get("/links/{short_code}/stats")
async def get_link_stat(short_code: str, db: AsyncSession = Depends(database.get_db)):
    link = await handlers.get_link_by_short_code(db, short_code)
    return link

@app.get("/links/search")
async def search_links(original_url: str, db: AsyncSession = Depends(database.get_db)):
    results = await handlers.get_link_by_origin(db,original_url)
    return results



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", log_level="info")