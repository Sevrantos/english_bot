from aiogram import Router


def setup_routers() -> Router:
    from . import admin, common, students

    router = Router()

    router.include_routers(
        common.router,
        admin.router,
        students.router,
    )

    return router
