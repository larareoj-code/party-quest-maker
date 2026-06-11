# Party Quest Maker Design QA

## Release checks

- Desktop layout: passed at 1440 x 1024.
- Mobile layout: passed at 375 x 844 with no horizontal overflow.
- Cover artwork: loaded and correctly framed.
- Quest generation: passed for repeated anonymous generations.
- Game modes: scavenger hunt, mini escape room, and party bingo rendered correctly.
- Premium prompts: print, host, and save actions show the lifetime tools offer.
- Billing: production checkout API returns a Stripe Checkout URL for the configured one-time price.
- Entitlement: validates app metadata, expected price, browser installation ID, payment completion, refunds, and disputes.
- Production health: `https://party-quest-maker.vercel.app/api/health` returns HTTP 200.

## Fixed before release

- Hidden radio inputs caused mobile horizontal scrolling.
- Checkout sessions from unrelated Stripe products could unlock the app.
- A delayed entitlement check could lose the returned session ID.
- Printable-pack copy exceeded the implemented print behavior.
- Vercel Python project metadata was incomplete.

## Result

Release passed. The free generator and paid lifetime tools have matching, traceable product claims.
