from src.support_chat import MarketplaceSupport


class FakeClient:
    def __init__(self):
        self.calls = []

    def create_channel(self, channel, channel_type, vendor):
        self.calls.append(("create", channel, channel_type, vendor))
        return {"ok": True, "data": {}}

    def issue_token(self, client_id, channels, capabilities, ttl_seconds):
        self.calls.append(("token", client_id, channels, capabilities, ttl_seconds))
        return {"ok": True, "data": {"token": "browser-token"}}

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel, event, data, account_id))
        return {"ok": True, "data": {}}

    def send_email(self, to, subject, body):
        self.calls.append(("email", to, subject, body))
        return {"ok": True, "data": {"message_id": "msg-1"}}


def test_buyer_update_is_published_and_handoff_is_emailed():
    order = {"order_id": "8842", "seller_id": "seller-42", "seller_email": "seller@example.com", "buyer_id": "buyer-17"}
    fake = FakeClient()
    support = MarketplaceSupport(fake)
    session = support.start_session(order)
    support.publish_buyer_update(order, "Where is my order?")
    handoff = support.finish_session(order, "Buyer: Where is my order?")

    assert session["channel"] == "marketplace-order-8842"
    assert session["token"]["token"] == "browser-token"
    assert fake.calls[2][2] == "buyer_update"
    assert fake.calls[2][3]["message"] == "Where is my order?"
    assert handoff["data"]["message_id"] == "msg-1"


def test_existing_channel_session_does_not_provision_resource():
    order = {"order_id": "8842", "channel": "existing-channel", "seller_id": "seller-42", "seller_email": "seller@example.com", "buyer_id": "buyer-17"}
    fake = FakeClient()

    session = MarketplaceSupport(fake).start_session(order, create_channel=False)

    assert session["channel"] == "existing-channel"
    assert fake.calls[0][0] == "token"
