from collections.abc import Callable
import gc

from django.apps import AppConfig
from django.conf import settings
from django.db.models import CharField, TextField
from django.utils.module_loading import import_string

from ..core.telemetry import initialize_telemetry
from .db.filters import PostgresILike


class CoreAppConfig(AppConfig):
    name = "saleor.core"

    def ready(self) -> None:
        from django.urls import get_resolver
        CharField.register_lookup(PostgresILike)
        TextField.register_lookup(PostgresILike)
        if settings.SENTRY_DSN:
            settings.SENTRY_INIT(settings.SENTRY_DSN, settings.SENTRY_OPTS)
        self.validate_jwt_manager()
        initialize_telemetry()
        getattr(get_resolver(settings.ROOT_URLCONF), "url_patterns")
        gc.collect()
        gc.freeze()

    def validate_jwt_manager(self) -> None:
        jwt_manager_path = getattr(settings, "JWT_MANAGER_PATH", None)
        if not jwt_manager_path:
            raise ImportError(
                "Missing setting value for JWT Manager path - JWT_MANAGER_PATH"
            )
        try:
            jwt_manager = import_string(jwt_manager_path)
        except ImportError as e:
            raise ImportError(f"Failed to import JWT manager: {e}.") from e

        validate_method: Callable[[], None] | None = getattr(
            jwt_manager, "validate_configuration", None
        )
        if validate_method is None:
            return
        validate_method()
