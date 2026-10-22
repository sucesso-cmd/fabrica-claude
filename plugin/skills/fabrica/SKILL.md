---
name: fabrica
description: Install (for one company or, on the agency plan, per client), configure, refresh the numbers of, or update Fábrica, the pixel-art factory that shows a company's funnel, bottleneck, delivery and team actions. Use when the user runs /fabrica, asks to install or set up Fábrica, to update its numbers, or to update the app.
---

# Fábrica

Fábrica is a single web page (index.html + fabrica.config.js) that draws the user's funnel as a pixel-art factory: each stage is a machine, each conversion a pipe, the worst pipe against its target is the clogged bottleneck. It reads its numbers from `dados.json`, a published Google Sheet (CSV) or Supabase.

The helper script `fabrica.py` lives in this skill's base directory. Run it with `python3 <base dir>/fabrica.py ...`. Talk to the user in their language. Keep it short: ask one thing at a time, offer defaults.

## 1. Install

1. Ask for the email used to subscribe. Run `fabrica.py install --email EMAIL --dir fabrica` in the user's current folder (ask first if they want another folder).
2. If it prints `LICENSE_FAIL`, tell the user plainly that no active Fábrica subscription was found for that email and give them https://fabrica-site-71s.pages.dev/en/#preco. Stop there.
3. If it prints `NEED_CLIENT`, the email has the agency plan: ask which client this factory is for and use the client install below.
4. On success, go to step 2. Never edit `index.html`.

### Agency plan: one factory per client

`/fabrica client "Client name"` (or the user says they are an agency installing for a client):

1. Ask for the agency email (once; reuse it for later clients in the same session) and the client name if missing.
2. Run `fabrica.py install --email EMAIL --client "Client name"`. It creates `fabrica-<client>/` in the current folder and sets `chave` in the config so several factories can live on one domain.
3. The output shows `clients_used` of `clients_limit`. Tell the user in one line (e.g. "3 of 10 client slots used"). Reinstalling or updating the same client does not use a slot.
4. If it prints `LICENSE_FAIL` with "limit reached", list the clients already installed (they are in the message) and tell the user to reply to their receipt to add slots. Stop.
5. Then do steps 2 to 4 for that client: the interview is about the client's funnel and team, and the numbers come from the client's tools or sheet. Owners can mix both teams (e.g. "Agency", "Front desk"). When publishing, suggest one link per client (e.g. `client.youragency.com`).

For later runs on a client, work inside that client's folder (`--dir fabrica-<client>`).

## 2. Short interview → fabrica.config.js

Start from `fabrica/fabrica.config.en.js` for English speakers (copy it over `fabrica.config.js`) or keep `fabrica.config.js` for Portuguese. Then ask, offering the current values as defaults:

- Company name and currency (USD, BRL, EUR).
- Funnel stages, 2 to 7, in order (default: Ads, Leads, Qualified, Booked, Showed up, Sales). For each stage after the first non-money one, the target conversion from the previous stage (defaults are in the file). Stage ids must be short lowercase words.
- Recurring revenue: on or off. If on: monthly revenue floor and target, and up to 4 delivery pillars (default Delivery late, Support unhappy, Results at risk).
- Team member names for the "owner" field.

Edit only the values in `fabrica.config.js`; keep its structure and comments.

## 3. Numbers

For every stage id the page needs `<id>.semana` (last 7 days) and `<id>.mes` (last 30 days); optional `<id>.fila` (people stuck before that machine, e.g. no-shows, open proposals). For recurring: `clientes`, `mrr`, and `<pillar>.ruins` / `<pillar>.total`. Money stages (`tipo: 'dinheiro'`) are amounts spent.

Pick the source, in this order:

1. **Tools already connected to Claude** (check which MCP tools you have: HubSpot, Pipedrive, Salesforce, Close, GoHighLevel, Stripe, Meta Ads, Google Ads, Google Sheets/Drive, Supabase/Postgres, Notion, Airtable). Map each stage to what the tool can count (e.g. HubSpot: contacts created = leads, lifecycle stage changes = qualified, meetings booked/completed, deals won; Meta Ads: spend; Stripe: active subscriptions and MRR). Show the user the mapping in one short table and confirm it before counting. Count both windows (7 and 30 days), write them to a temporary JSON (`{"leads": {"semana": 214, "mes": 900}, ...}`) and run `fabrica.py numbers --file that.json --dir fabrica`.
2. **A spreadsheet they already keep**: help them create a Google Sheet from `fabrica/planilha-modelo.csv` (columns `chave`, `valor`), publish it as CSV, and set `fonte: { tipo: 'planilha', url: '<csv link>' }`.
3. **They just tell you the numbers**: write them with `fabrica.py numbers`.

Then run `fabrica.py check --dir fabrica`; if `faltando` lists stage ids, fix the mapping or ask for those numbers. Never invent numbers. If a stage cannot be counted, say so and leave it out of the funnel or ask the user.

## 4. Open and share

- Local: run `fabrica/iniciar.sh` in the background (Windows: `iniciar.bat`) and give the user http://localhost:8080.
- For the team, offer (and only do it after they say yes, since it publishes a page on the internet): `npx wrangler pages deploy fabrica --project-name <name>` if they use Cloudflare, or `npx netlify-cli deploy --dir fabrica --prod` if they use Netlify, or drag the folder to app.netlify.com/drop. Remind them that with `json` or `planilha` the numbers in the page are visible to anyone with the link; for a private board use the Supabase option in `fabrica/README.md` (it adds an access code).

## 5. Later runs

- `/fabrica numbers`: recount with the same mapping (it is the same tools and the same definitions; save the mapping in `fabrica/.fabrica-mapa.json` the first time so later runs reuse it) and run `fabrica.py numbers`.
- `/fabrica update`: run `fabrica.py update --dir fabrica` (agencies: once per `fabrica-<client>` folder). It keeps their config, numbers and actions. If it prints `LICENSE_FAIL`, the subscription is no longer active: tell them, the current version keeps working but will not update.
- Suggest a weekly refresh. If the user wants it automatic, offer a scheduled task that runs `/fabrica numbers` every Monday.

## Rules

- The subscription is checked by the server; do not try to bypass it or download the app from anywhere else.
- Never put API keys, tokens or passwords in `fabrica.config.js`, `dados.json` or the published folder (the Supabase anon/publishable key is the only exception, as the README explains).
- Keep the user's actions: never delete `dados.json` actions or the Supabase table.
