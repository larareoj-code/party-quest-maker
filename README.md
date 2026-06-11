# Party Quest Maker

Party Quest Maker creates personalized scavenger hunts, mini escape-room packs, and party bingo games for birthdays, family gatherings, date nights, showers, reunions, and team celebrations.

## Product model

- Free: unlimited on-screen quest creation.
- Lifetime tools: `$19` one-time payment for browser-local saves, complete print packs, and host mode.
- No account required. Payment is handled by Stripe Checkout.
- Saved quests remain in the buyer's browser and can be deleted at any time.

## Safety

The deterministic generator excludes challenges involving strangers, trespassing, climbing, dangerous food, regulated advice, or copyrighted characters. Hosts remain responsible for checking age and location suitability before play.

## Local development

```powershell
python -m pytest
python scripts/serve.py --port 8802
```
