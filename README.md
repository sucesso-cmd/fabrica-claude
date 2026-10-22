# Fábrica for Claude

Let Claude install [Fábrica](https://fabrica-site-71s.pages.dev/en/), the pixel-art factory of your funnel, in one command.
Claude checks your subscription, downloads the app, asks about your funnel, pulls the numbers from the tools you already
connected (HubSpot, Pipedrive, Stripe, Meta Ads, Google Sheets…) and opens your factory.

```bash
claude plugin marketplace add sucesso-cmd/fabrica-claude && claude plugin install fabrica@fabrica
```

Then, inside Claude Code:

```
/fabrica            install or set up
/fabrica numbers    refresh the numbers
/fabrica update     get the latest version (keeps your config and actions)
```

Needs an active Fábrica subscription (US$ 9/month for founding members): https://fabrica-site-71s.pages.dev/en/#preco
This repository only holds the installer. The app is downloaded after the subscription check.
