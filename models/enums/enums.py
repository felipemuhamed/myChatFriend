from enum import Enum


class PlanoEnum(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"


class AssinaturaStatusEnum(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"