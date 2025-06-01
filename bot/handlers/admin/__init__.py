from aiogram import Router

from bot.middlewares.is_admin import IsAdminMiddleware
from bot.utils.config import ADMIN_IDS

from .classes import router as classes_router
from .lessons import router as lessons_router
from .materials import router as materials_router
from .topics import router as topics_router

router = Router()

router.message.middleware(IsAdminMiddleware(ADMIN_IDS))
router.callback_query.middleware(IsAdminMiddleware(ADMIN_IDS))

router.include_routers(
    materials_router,
    lessons_router,
    topics_router,
    classes_router,
)
