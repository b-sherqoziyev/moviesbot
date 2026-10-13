"""Movies Reel — Yagona maxsus istisnolar iyerarxiyasi."""


class MoviesBotException(Exception):
    """Barcha loyiha xatolarining asosiy klassi."""
    def __init__(self, message: str = "Tizimda xatolik yuz berdi"):
        self.message = message
        super().__init__(self.message)


class MovieNotFoundError(MoviesBotException):
    """Film topilmaganda yuzaga keladigan xatolik."""
    def __init__(self, code: str):
        super().__init__(f"Film topilmadi: {code}")
        self.code = code


class SubscriptionRequiredError(MoviesBotException):
    """Majburiy kanallarga a'zo bo'lmaganda yuzaga keladigan xatolik."""
    def __init__(self, unsubscribed_channels: list):
        super().__init__("Majburiy kanallarga a'zo bo'lish talab qilinadi")
        self.unsubscribed_channels = unsubscribed_channels


class AccessDeniedError(MoviesBotException):
    """Ruxsat yetarli bo'lmaganda yuzaga keladigan xatolik (RBAC)."""
    def __init__(self, permission: str):
        super().__init__(f"Amalni bajarish uchun huquq yetarli emas: {permission}")
        self.permission = permission


class BroadcastError(MoviesBotException):
    """Xabar tarqatishda yuzaga keladigan xatolik."""
    pass
