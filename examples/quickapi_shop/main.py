"""Optional future integration example.

SQLNocturne is independent. This file shows how a web framework could consume
its Result object, but SQLNocturne does not depend on QuickAPI.
"""

from sqlnocturne import Database
from sqlnocturne.integrations.quickapi import nocturne_response


db = Database("sqlite:///shop.db")


def list_products_handler():
    result = db.table("products").select("id", "name", "price").limit(20).result()
    return nocturne_response(result)


if __name__ == "__main__":
    print(list_products_handler())
