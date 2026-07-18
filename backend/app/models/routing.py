from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import HttpUrl, SecretStr

from backend.app.config.model_settings import ModelSettings, ProviderName


@dataclass(frozen=True, slots=True)
class ResolvedModelRoute:
    provider: ProviderName
    model: str
    base_url: HttpUrl
    api_key: SecretStr = field(repr=False)


@dataclass(frozen=True, slots=True)
class ModelRoutes:
    intent: tuple[ResolvedModelRoute, ...]
    explanation: tuple[ResolvedModelRoute, ...]
    extraction: tuple[ResolvedModelRoute, ...]
    judge: tuple[ResolvedModelRoute, ...]


class ModelRoutingError(RuntimeError):
    """Raised when configured model roles cannot form valid routes."""


def _resolved_route(settings: ModelSettings, role_name: str) -> ResolvedModelRoute:
    role = getattr(settings, role_name)
    connection = settings.connection_for(role.provider)
    return ResolvedModelRoute(
        provider=role.provider,
        model=role.model,
        base_url=connection.base_url,
        api_key=connection.api_key,
    )


def _reject_duplicate_roles(
    first_name: str,
    first: ResolvedModelRoute,
    second_name: str,
    second: ResolvedModelRoute,
) -> None:
    if (first.provider, first.model) == (second.provider, second.model):
        raise ModelRoutingError(
            f"Duplicate model routes for roles: {first_name}, {second_name}"
        )


def resolve_model_routes(settings: ModelSettings) -> ModelRoutes:
    main = _resolved_route(settings, "main")
    extraction = _resolved_route(settings, "extraction")
    fallback = _resolved_route(settings, "fallback")
    judge = _resolved_route(settings, "judge")

    _reject_duplicate_roles("main", main, "fallback", fallback)
    _reject_duplicate_roles("extraction", extraction, "fallback", fallback)

    main_routes = (main, fallback)
    return ModelRoutes(
        intent=main_routes,
        explanation=main_routes,
        extraction=(extraction, fallback),
        judge=(judge,),
    )
