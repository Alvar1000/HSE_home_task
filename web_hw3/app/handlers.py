import aioredis
from sqlalchemy import select, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
import schemas
import models
import secrets
import string
from datetime import datetime, timedelta


def generate_short_code(length = 6):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))



async def create_link(db: AsyncSession, link: schemas.LinkCreate):
    short_code = link.custom_alias or generate_short_code()
    new_link = models.Link(
        original_url = str(link.original_url),
        short_code = short_code,
        expires_at = link.expires_at,
        custom_alias = link.custom_alias
    )

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return {"short_code": short_code}

async def get_link_by_short_code(db: AsyncSession, short_code: str ):
    query = await db.execute(select(models.Link).where(models.Link.short_code == short_code))
    return query.scalar_one_or_none()

async def get_link_deleted(db:AsyncSession, short_code: str ):
    result = await db.execute(select(models.Link).where(models.Link.short_code == short_code))
    link = result.scalar_one_or_none()

    if link:
        await db.delete(link)
        await db.commit()

async def get_link_by_origin(db: AsyncSession, original_url = str):
    query = await db.execute(select(models.Link).where(models.Link.original_url.contains(original_url)))
    return query.scalars().all()


async def increment_link_clicks(db: AsyncSession, link: models.Link):
    link.clicks += 1
    link.last_accessed_at = datetime.utcnow().date()
    await db.commit()
    return link

async def update_link(db: AsyncSession, short_code: str, new_url: str ):
    result = await db.execute(select(models.Link).where(models.Link.short_code == short_code))
    result.original_url = new_url
    await db.commit()

async def purge_old_links(db: AsyncSession):
    current_date = datetime.utcnow().date()
    await db.execute(
        delete(models.Link).where(
            or_(
                models.Link.expires_at <= current_date,
                and_(
                    models.Link.last_accessed_at.is_not(None),
                    models.Link.last_accessed_at <= current_date - timedelta(days=90)
                )
            )
        )
    )
    await db.commit()


async def cache_popular_links(db: AsyncSession, redis: aioredis.Redis, limit: int = 100):
    popular_links = await db.execute(
        select(models.Link)
        .order_by(models.Link.clicks.desc())
        .limit(limit)
    )

    for link in popular_links.scalars():
        await redis.setex(
            f"popular:{link.short_code}",
            86400,
            link.original_url
        )