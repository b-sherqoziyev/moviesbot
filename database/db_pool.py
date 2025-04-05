import asyncpg
import logging

logger = logging.getLogger(__name__)

async def init_db_pool(db_name, db_user, db_password, db_host, db_port):
    try:
        pool = await asyncpg.create_pool(
            database=db_name, user=db_user,
            password=db_password, host=db_host, port=db_port,
            min_size=1, max_size=10
        )
        logger.info("Ma'lumotlar bazasi pooli muvaffaqiyatli ishga tushdi.")
        return pool
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasi poolini ishga tushirishda xato: {e}")
        raise