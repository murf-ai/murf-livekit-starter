import json
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

DEFAULT_CATALOGUE_PATH = Path(__file__).with_name("catalogue.json")
DEFAULT_CATALOGUE_API_URL = "http://127.0.0.1:8001/catalogue"
CATALOGUE_TIMEOUT_SECONDS = 2.0


class CatalogueUnavailableError(RuntimeError):
    """Raised when the prototype catalogue cannot be read or validated."""


@dataclass(frozen=True)
class CatalogueItem:
    product_id: str
    name: str
    seller: str
    location: str
    category: str
    price_inr: int
    stock_quantity: int
    unit: str

    @property
    def available(self) -> bool:
        return self.stock_quantity > 0


@dataclass(frozen=True)
class Catalogue:
    updated_at: str
    products: tuple[CatalogueItem, ...]


@dataclass(frozen=True)
class OrderLine:
    product_id: str
    name: str
    quantity: int
    unit_price_inr: int
    subtotal_inr: int


@dataclass(frozen=True)
class OrderTotal:
    lines: tuple[OrderLine, ...]
    total_inr: int
    updated_at: str


def _parse_catalogue(payload: object) -> Catalogue:
    if not isinstance(payload, dict):
        raise ValueError("catalogue response must be an object")
    updated_at = payload["updated_at"]
    products = tuple(CatalogueItem(**product) for product in payload["products"])
    if not isinstance(updated_at, str) or not updated_at or not products:
        raise ValueError("missing catalogue metadata or products")
    return Catalogue(updated_at=updated_at, products=products)


def load_catalogue(path: str | Path = DEFAULT_CATALOGUE_PATH) -> Catalogue:
    """Load and validate the hand-built dataset used by the catalogue API."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return _parse_catalogue(payload)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise CatalogueUnavailableError(
            "The local catalogue is temporarily unavailable. I can't reliably "
            "confirm current prices or stock right now."
        ) from exc


def fetch_catalogue(
    url: str = DEFAULT_CATALOGUE_API_URL,
    timeout: float = CATALOGUE_TIMEOUT_SECONDS,
) -> Catalogue:
    """Fetch and validate catalogue data from the separately managed HTTP API."""
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _parse_catalogue(payload)
    except (TimeoutError, socket.timeout) as exc:
        raise CatalogueUnavailableError(
            "The local commerce catalogue took too long to respond, so I can't "
            "confirm the current price or stock right now."
        ) from exc
    except URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            raise CatalogueUnavailableError(
                "The local commerce catalogue took too long to respond, so I can't "
                "confirm the current price or stock right now."
            ) from exc
        raise CatalogueUnavailableError(
            "The local catalogue is temporarily unavailable. I can't reliably "
            "confirm current prices or stock right now."
        ) from exc
    except (
        HTTPError,
        OSError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise CatalogueUnavailableError(
            "The local catalogue is temporarily unavailable. I can't reliably "
            "confirm current prices or stock right now."
        ) from exc


def search_products(
    catalogue: Catalogue,
    query: str = "",
    category: str = "",
    max_price: int | None = None,
) -> list[CatalogueItem]:
    query_terms = query.casefold().strip().split()
    category_terms = category.casefold().replace("-", " ").strip().split()
    matches = []
    for product in catalogue.products:
        searchable = (
            f"{product.product_id} {product.name} {product.seller} {product.category}"
        ).casefold()
        if query_terms and not all(term in searchable for term in query_terms):
            continue
        if (
            not query_terms
            and category_terms
            and not any(term in product.category.casefold() for term in category_terms)
        ):
            continue
        if max_price is not None and product.price_inr > max_price:
            continue
        matches.append(product)
    return matches


def calculate_total(
    catalogue: Catalogue,
    product_ids: list[str],
    quantities: list[int],
) -> OrderTotal:
    if not product_ids:
        raise ValueError("The order is empty; provide at least one product.")
    if len(product_ids) != len(quantities):
        raise ValueError("Each product must have one corresponding quantity.")

    products_by_id = {
        product.product_id.casefold(): product for product in catalogue.products
    }
    lines = []
    for product_id, quantity in zip(product_ids, quantities, strict=True):
        product = products_by_id.get(product_id.casefold().strip())
        if product is None:
            raise ValueError(f"Product {product_id} was not found in the catalogue.")
        if quantity <= 0:
            raise ValueError(f"Quantity for {product.name} must be greater than zero.")
        if quantity > product.stock_quantity:
            raise ValueError(
                f"Insufficient stock for {product.name}; only "
                f"{product.stock_quantity} {product.unit}(s) are available."
            )
        lines.append(
            OrderLine(
                product_id=product.product_id,
                name=product.name,
                quantity=quantity,
                unit_price_inr=product.price_inr,
                subtotal_inr=product.price_inr * quantity,
            )
        )
    return OrderTotal(
        lines=tuple(lines),
        total_inr=sum(line.subtotal_inr for line in lines),
        updated_at=catalogue.updated_at,
    )
