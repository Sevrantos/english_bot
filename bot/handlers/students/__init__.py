from aiogram import Router

from .lessons import router as lessons_router
from .menu import router as menu_router
from .quizzes import router as quiz_router
from .registration import router as registration_router
from .support import router as support_router
from .tests import router as test_router

router = Router()

router.include_routers(
    registration_router,
    support_router,
    quiz_router,
    test_router,
    lessons_router,
    menu_router,
)
