from aiogram import Router

from . import start, menu, settings, payment, features, admin, generate, uploads

router = Router()
router.include_router(start.router)
router.include_router(menu.router)
router.include_router(settings.router)
router.include_router(payment.router)
router.include_router(features.router)
router.include_router(admin.router)
router.include_router(generate.router)
# uploads.router is last: it has catch-all photo/document/text handlers that
# must not shadow the more specific handlers registered above.
router.include_router(uploads.router)
