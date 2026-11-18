import argparse
from typing import Any

try:
    from .infrai_client import InfraiClient
except ImportError:
    from infrai_client import InfraiClient


class MarketplaceSupport:
    def __init__(self, client: InfraiClient):
        self.client = client

    def start_session(self, order: dict[str, Any], create_channel: bool = True) -> dict[str, Any]:
        channel = order.get("channel", f"marketplace-order-{order['order_id']}")
        if create_channel:
            self.client.create_channel(channel, "private", "marketplace")
        token = self.client.issue_token(
            order["buyer_id"], [channel], ["publish", "subscribe"], 900
        )
        return {"channel": channel, "token": token["data"]}

    def publish_buyer_update(self, order: dict[str, Any], message: str) -> dict[str, Any]:
        channel = order.get("channel", f"marketplace-order-{order['order_id']}")
        return self.client.publish(
            channel,
            "buyer_update",
            {"order_id": order["order_id"], "message": message, "request_id": f"{order['order_id']}:buyer_update"},
            order["seller_id"],
        )

    def finish_session(self, order: dict[str, Any], transcript: str) -> dict[str, Any]:
        return self.client.send_email(
            order["seller_email"],
            f"Support transcript for order {order['order_id']}",
            transcript,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seller-email", required=True)
    parser.add_argument("--channel", required=True)
    args = parser.parse_args()
    order = {"order_id": "8842", "channel": args.channel, "seller_id": "seller-42", "seller_email": args.seller_email, "buyer_id": "buyer-17"}
    support = MarketplaceSupport(InfraiClient())
    session = support.start_session(order, create_channel=False)
    support.publish_buyer_update(order, "The buyer asked for a delivery update.")
    email = support.finish_session(order, "Buyer: Is the parcel on the way?\nSeller: I will check the carrier now.")
    print({"channel": session["channel"], "token": session["token"], "message_id": email["data"]["message_id"]})


if __name__ == "__main__":
    main()
