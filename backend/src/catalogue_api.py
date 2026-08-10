import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from catalogue import DEFAULT_CATALOGUE_PATH, CatalogueUnavailableError, load_catalogue

logger = logging.getLogger("catalogue-api")


class CatalogueRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path != "/catalogue":
            self._send_json(404, {"error": "Not found"})
            return
        try:
            catalogue = load_catalogue(DEFAULT_CATALOGUE_PATH)
        except CatalogueUnavailableError as exc:
            self._send_json(503, {"error": str(exc)})
            return
        self._send_json(
            200,
            {
                "updated_at": catalogue.updated_at,
                "products": [
                    {
                        "product_id": product.product_id,
                        "name": product.name,
                        "seller": product.seller,
                        "location": product.location,
                        "category": product.category,
                        "price_inr": product.price_inr,
                        "stock_quantity": product.stock_quantity,
                        "unit": product.unit,
                    }
                    for product in catalogue.products
                ],
            },
        )

    def log_message(self, message: str, *args: object) -> None:
        logger.info("%s - %s", self.client_address[0], message % args)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    host = os.getenv("CATALOGUE_API_HOST", "127.0.0.1")
    port = int(os.getenv("CATALOGUE_API_PORT", "8001"))
    server = ThreadingHTTPServer((host, port), CatalogueRequestHandler)
    logger.info("Catalogue API listening on http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Catalogue API stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
