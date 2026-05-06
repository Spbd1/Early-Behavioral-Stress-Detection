"""Ontology categories for behavioral stress keyword governance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class OntologyCategory:
    """Human-readable keyword ontology category metadata."""

    key: str
    label: str
    description: str
    default_expected_direction_under_stress: str
    inclusion_guidance: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)


class KeywordOntologyManager:
    """Manage the controlled ontology used to constrain keyword expansion."""

    def __init__(self, categories: list[OntologyCategory] | None = None) -> None:
        self._categories = {
            category.key: category for category in categories or default_categories()
        }

    @property
    def categories(self) -> dict[str, OntologyCategory]:
        """Return ontology categories keyed by stable category id."""
        return dict(self._categories)

    def get(self, key: str) -> OntologyCategory:
        """Return one category or raise a clear error for unsupported categories."""
        if key not in self._categories:
            supported = ", ".join(sorted(self._categories))
            raise ValueError(
                f"Unsupported ontology category '{key}'. Supported categories: {supported}"
            )
        return self._categories[key]

    def validate_category(self, key: str) -> bool:
        """Validate that a category id is part of the controlled ontology."""
        self.get(key)
        return True

    def expected_direction(self, key: str) -> str:
        """Return the default expected direction under stress for a category."""
        return self.get(key).default_expected_direction_under_stress

    def to_dict(self) -> dict[str, Any]:
        """Return serializable ontology payload."""
        return {key: category.to_dict() for key, category in self._categories.items()}


def default_categories() -> list[OntologyCategory]:
    """Build the required controlled keyword ontology categories."""
    return [
        OntologyCategory(
            key="discretionary_contraction",
            label="discretionary contraction",
            description=(
                "Reduced interest in optional spending, travel, entertainment, "
                "and non-essential services."
            ),
            default_expected_direction_under_stress="increase_for_savings_terms_or_decrease_for_spend_terms",
            inclusion_guidance=(
                "Prefer phrases that reveal delayed, canceled, or cheaper discretionary choices."
            ),
        ),
        OntologyCategory(
            key="repair_vs_replacement",
            label="repair vs replacement",
            description=(
                "Consumers searching to fix, service, mend, or extend life instead of buying new."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Include local repair/service terms when grounded by maintenance "
                "or replacement contexts."
            ),
        ),
        OntologyCategory(
            key="discount_seeking",
            label="discount-seeking",
            description=(
                "Searches for coupons, deals, promotions, clearance, price "
                "matching, and low-cost vendors."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Favor terms with explicit value-seeking intent and avoid generic "
                "brand popularity terms."
            ),
        ),
        OntologyCategory(
            key="debt_stress",
            label="debt stress",
            description=(
                "Interest in arrears, minimum payments, refinancing, debt relief, "
                "collections, and credit strain."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Keep aggregate, non-diagnostic wording; exclude individual "
                "profiling or medical claims."
            ),
        ),
        OntologyCategory(
            key="layoffs",
            label="layoffs",
            description=(
                "Signals tied to job loss, redundancy, unemployment claims, "
                "severance, and layoff news."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Separate employer/news spikes from durable household stress "
                "indicators during review."
            ),
        ),
        OntologyCategory(
            key="inflation_anxiety",
            label="inflation anxiety",
            description=(
                "Concern about prices, cost of living, bills, rent, groceries, and affordability."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Require grounding in price pressure rather than general macro curiosity."
            ),
        ),
        OntologyCategory(
            key="substitution_behavior",
            label="substitution behavior",
            description=(
                "Trading down from premium to private-label, used, secondhand, "
                "generic, or lower-cost alternatives."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Include explicit swap/downshift language and locally relevant substitutes."
            ),
        ),
        OntologyCategory(
            key="micro_luxury_persistence",
            label="micro-luxury persistence",
            description=(
                "Small affordable treats that persist or rise even as larger purchases contract."
            ),
            default_expected_direction_under_stress="increase_or_stable",
            inclusion_guidance=(
                "Treat as ambiguous; require review because persistence can "
                "reflect culture or seasonality."
            ),
        ),
        OntologyCategory(
            key="regional_economic_anxiety",
            label="regional economic anxiety",
            description=(
                "Place-specific concern about local industries, closures, taxes, "
                "utility costs, and regional outlook."
            ),
            default_expected_direction_under_stress="increase",
            inclusion_guidance=(
                "Require geographic grounding and stable place codes where possible."
            ),
        ),
        OntologyCategory(
            key="location_specific_consumer_stress_signals",
            label="location-specific consumer stress signals",
            description=(
                "Local phrases tied to transport, housing, weather, industry, "
                "or services that proxy consumer stress."
            ),
            default_expected_direction_under_stress="context_dependent",
            inclusion_guidance=(
                "Must cite local context and be reviewed for volume, language, "
                "and provider support."
            ),
        ),
    ]
