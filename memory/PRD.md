# Frostfish — PRD

## Original problem statement (TR, summarized)
Move the repo https://github.com/Dostarki/fishesrh1 to Emergent (FastAPI + MongoDB). Remove X, the Early Access campaign and the points system entirely. What remains is the game plus wallet sign-in through RainbowKit with a SIWE signature on Robinhood Chain Mainnet (4663, RPC https://rpc.mainnet.chain.robinhood.com). Wallet required, no guest mode; wrong network locks the game. Game sessions per wallet in MongoDB. Nonce single-use, domain + chainId checked. Signed session lasts 24 hours.

### Iteration 2 (2026-06) — real token economy
- Demo TOKEN economy removed. Fishermen are bought with the real $FISHESRH ERC-20 (CA 0x098e9efbf4d65cbfc27130c1bf8a09b007659dbf) at $1 (Angler) / $10 (Netter) / $50 (Captain); tokens are transferred to the treasury 0x603a26e0745aE579ad0F931307a386ddC3DD096F. User signs the transfer in the wallet; backend verifies the tx receipt (Transfer log from wallet → treasury, amount ≥ 98% of quote, tx hash single-use) before granting the fisherman.
- Insufficient balance → player is sent to https://ponsfamily.com/launchpad/<CA>.
- Token USD price = Ponsfamily bonding-curve `getReserves()` (curve 0x138b88…53e9) × ETH/USD (CoinGecko, fallback Ponsfamily page `quoteUsd`); if graduated/unavailable → Ponsfamily page `priceUsd`; admin manual override possible.
- Earnings shown per HOUR; every fisherman pays back its price in 48h (hourly_usd = price/48). Earnings tracked in USD, paid in tokens at live price via Claim (min $0.05). Purchases are permanent and stored in MongoDB (`purchases`, worker on `games`).
- Hidden admin panel `/errorlogin404495959`, password `FISHESPRO4488` (env ADMIN_PASSWORD): edit token CA, treasury, curve, launchpad link, prices, manual price; paste a Ponsfamily link → "Read" auto-fills CA + curve. Shows live price, treasury balances, purchases, claims.
- Bug fixes: MetaMask SDK crash `(0, import_openapi_fetch.default) is not a function` (CRA had no loader for `.cjs` → craco alias to ESM build); SIWE signature now requested automatically right after wallet connect; sign-out also disconnects the wallet. Wallet addresses upserted into `wallets` on every login.

### Iteration 3 (2026-06) — username
- After wallet connect + SIWE, a non-closable "Pick your name." dialog (UsernameGate.jsx) asks for a username (3–16, A-Z a-z 0-9 _, unique case-insensitive, set once). POST /api/profile/username stores it in `wallets.username` and `games.name` / `username_set`. The leaderboard only lists players who have a username (ties broken by session_id). Returning users keep their name.

### Iteration 4 (2026-06) — game access (paid entry + closed beta)
- Admin panel "Game access": **Paid entry** toggle + **Entry fee (USD)**. When on, every wallet pays ONCE (bilet mantığı) in native ETH on Robinhood Chain to the treasury: POST /api/entry/quote (USD→wei at CoinGecko ETH/USD) → wallet `sendTransaction` → POST /api/entry/confirm verifies receipt (from=wallet, to=treasury, status 1, value ≥ 98% quote, tx hash single-use) → `wallets.entry_paid_at`, `games.entry_paid`, `entry_payments`. Unpaid wallets get EntryGate.jsx (non-closable) and 402 on purchase/claim/username. Game state exposes `entry_required`, `entry_paid`, `entry_fee_usd`.
- **Beta participants only** toggle: when on, SIWE verify returns 403 for wallets not in `beta_wallets`. CSV import (POST /api/admin/beta/import, multipart) extracts every 0x… address from any column, dedupes, and REPLACES the list; DELETE /api/admin/beta/{address}, DELETE /api/admin/beta (clear). Listed wallets skip the entry fee while the beta list is active (user choice).
- Settings keys: entry_fee_enabled, entry_fee_usd, beta_enabled. /api/config exposes entryFeeEnabled/entryFeeUsd/betaEnabled. Admin stats show entry tickets.


- backend/server.py: SIWE auth, /api/config, /api/entry/quote|confirm, /api/purchase/quote|confirm, /api/claim, /api/claims, /api/game, /api/leaderboard. backend/access.py: beta whitelist + needs_entry + CSV parsing. backend/admin.py: /api/admin/* (login w/ lockout, settings, resolve, stats, beta list/import/remove/clear). backend/pricing.py: settings + price cache. backend/chain.py: raw JSON-RPC (eth_call, receipts, signed ERC-20 transfer for claims). backend/game.py: economy (grant, fish_value_usd, public_state). backend/db.py: Mongo client.
- frontend: index.js routes (`/` game, `/errorlogin404495959` AdminPage); hooks/useEconomy.js (config, wagmi balanceOf/transfer); hooks/useGame.js (quote/confirmPurchase/claim/entryQuote/confirmEntry); hooks/useEntryFee.js (ETH payment + pending persistence); components/EntryGate.jsx, UsernameGate.jsx, AdminBeta.jsx; components/InfoDialogs.jsx (Market/Inventory/Guide); GameChrome.jsx TopHUD; PlayGate auto-sign; pages/AdminPage.jsx; economy.css.
- Collections: games, wallets, wallet_sessions, wallet_challenges, purchase_quotes, purchases, claims, entry_quotes, entry_payments, beta_wallets, settings (economy singleton), admin_sessions, admin_attempts.

## Env (backend/.env)
MONGO_URL, DB_NAME, CORS_ORIGINS, ROBINHOOD_CHAIN_ID=4663, APP_URL, ROBINHOOD_RPC_URL, ADMIN_PASSWORD, TREASURY_PRIVATE_KEY (optional; enables Claim — collected via secrets).

## Testing
- iteration_1 (2026-06): 18/18 backend pytest + full frontend flow with mock wallet passed. Real on-chain purchase/claim not executed in tests (test wallet has no funds).
- iteration_2 (2026-06): game access — 21/21 backend pytest (tests/test_frostfish_access.py + username) + admin UI (toggles, CSV import, list) + EntryGate / closed-beta error in game UI passed. Real ETH entry payment not executed (no funds).
- iteration_3 (2026-06): OpenSea NFT holder gate — 29/29 backend pytest (tests/test_frostfish_nft_gate.py + previous) + admin UI (Read link, card, check wallet, toggles) + closed-beta message/link in game passed.

### Iteration 5 (2026-06) — OpenSea NFT gate + page title
- Admin "NFT holders can join the beta" toggle + OpenSea link "Read" (public OpenSea v2 API: collection or item link → name, image, chain, contract, standard, supply; saved as settings.nft_gate). While beta is on, wallets not on the CSV list but holding ≥1 NFT (balanceOf via the NFT chain's public RPC, 5-min cache) sign in and skip the entry fee. Admin "Check a wallet" tool; /api/config.betaNft shown as link in PlayGate error. Upstream errors now 400 (ingress turns 502 into HTML).
- Browser tab title set to "FishesRH - BetaV1" (frontend/public/index.html).

## Backlog
- P0: Set TREASURY_PRIVATE_KEY (secret) so Claim works; treasury needs ETH for gas + FISHESRH balance. User to test a real $1 purchase.
- P1: Add preview/production domains in the Reown dashboard (user action).
- P1: Post-graduation pricing: after the curve graduates, price comes from the Ponsfamily page; consider DEX pool pricing.
- P2: Claim history UI in inventory; purchase receipts (explorer links) in inventory.
