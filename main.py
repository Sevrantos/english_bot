import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher

from bot.handlers import setup_routers
from bot.services.database.connection import Database
from bot.services.database.storage import PGStorage
from bot.utils import config
from web.server import app


async def main():
    db = Database(config.DSN)
    await db.connect()
    storage = PGStorage(db.pool)
    await storage.init_tables()

    bot = Bot(token=config.TOKEN)
    dp = Dispatcher(storage=storage)
    dp["db"] = db

    dp.include_router(setup_routers())

    web_server_task = asyncio.create_task(run_web_server())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        await db.disconnect()
        logging.info("Database connection closed.")

        web_server_task.cancel()


async def run_web_server():
    """Function to run the FastAPI server using uvicorn"""
    logging.info("Starting web server...")
    # Instead of using `uvicorn.run()`, you can use `await` here with the `Server`
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
