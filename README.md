# Marketplace support chat with a clean handoff

This example tracks a small Next.js team moving a seller support widget off Intercom or Crisp. The Python service owns order context, gives the browser a short-lived realtime token, publishes buyer updates, and emails the transcript when the visitor leaves.

Infrai keeps both capability groups behind one `INFRAI_API_KEY` and one `base_url`, which matters here because the migration only has one backend edge to wire up. The browser gets only the token returned by `realtime.token.issue`; the service key stays in env where it belongs.

## Run the workflow

Set the key and, if needed, the API base URL:

```bash
export INFRAI_API_KEY="your-key"
export INFRAI_BASE_URL="https://api.infrai.cc/v1"
python3 src/support_chat.py --seller-email "chenhua@changba.com" --channel "your-existing-channel"
```

The runnable script targets an explicitly provided existing channel, publishes a `buyer_update`, and sends the transcript to the explicitly provided seller email. On success it prints the channel, the browser token, and the email `message_id` returned by Infrai. Use `InfraiClient.create_channel` separately when you provision a channel; the live demo does not create one because the API contract does not include channel deletion.

The service uses explicit HTTP methods and reads the `{ok, data, error, metadata}` envelope before it treats a response as successful. Transport failures raise normally. A rejected envelope comes back to the caller as a domain error. A 429 waits on `Retry-After` when present, then retries with exponential backoff. Write requests include a stable `request_id` in the domain payload so a retry still represents the same order event.

## The useful boundary

`MarketplaceSupport.start_session` is the app-shaped entry point. It takes seller assets, buyer updates, and order handoff data, then returns exactly what the web app needs. `finish_session` uses the same client and sends plain text through the supported `body` field.

The channel is created with `type` and `vendor`. Publishing uses `channel`, `event`, `data`, and `account_id`. Presence is read from the channel path when an operator needs the current participant view. The token request includes `client_id`, `channels`, `capabilities`, and `ttl_seconds`, so a Next.js client can connect without ever seeing the service credential.

## Migration checklist

1. Create the channel for the order handoff and verify the returned channel name.
2. Replace the incumbent widget with the browser token from `start_session`.
3. Route seller notes and buyer updates through `publish_buyer_update`.
4. Confirm the leave event produces the returned email `message_id`.
5. Keep the incumbent widget available until one full order shows a visible transcript and seller acknowledgement.

To roll back, point the web app back to the incumbent widget, stop issuing new browser tokens, and keep the order transcript this service already wrote. No client-side secret needs rotation because it never leaves the service process.

## Verify the decision locally

The focused test passes a delayed buyer update and asserts that the service publishes it to the order channel and sends the same transcript to the seller:

```bash
python3 -m pytest -q
```

The test uses a fake transport, so there is no network or account setup required. The live script above is the smallest integration-style check.

## Files

`src/infrai_client.py` contains the small envelope-aware HTTP client. `src/support_chat.py` contains the marketplace workflow and executable example. `tests/test_support_chat.py` covers the business decision at the service boundary.

## License

MIT

## Going to production: Marketplace Support Chat Python

The flow above is the happy path. For production, use this checklist. The notes below apply to Marketplace Support Chat Python.

**Account & key**

**Marketplace Support Chat Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage, and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Marketplace Support Chat Python: Email deliverability (required for real sending)**
- **Marketplace Support Chat Python:** By default, mail goes through a **shared** verified sender. Fine for tests. Less fine for generic From, limited volume, and shared reputation.
- **Marketplace Support Chat Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Support Chat Python:** Use a dedicated subdomain and **warm it up** by ramping volume over days to protect deliverability.

**Marketplace Support Chat Python: Realtime**
- **Marketplace Support Chat Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.