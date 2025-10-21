## LiquorStoreMarketingAgent

Strategic, analytical, creative agent focused on profitable growth for liquor retail across in-store, ecommerce (City Hive), and delivery platforms (DoorDash/Uber/Instacart). Executes data-driven campaigns with ruthless ROI discipline.

### Features
- Customer segmentation (RFM, simple heuristics)
- Campaign planning (4-week rolling calendar, briefs, promo codes)
- Promo optimization with margin guardrails
- Content generation (email/SMS/social) with built-in compliance notes
- Simple attribution analysis and budget reallocation guidance
- Loyalty engine scaffolding (points, tiers, referrals)

### Project layout
```
/agent
  __init__.py
  __main__.py        # python -m agent
  agent.py           # core agent orchestration and modules
  cli.py             # CLI entrypoint
/data/demo           # sample JSON data to run locally
/out                 # optional outputs
```

### Requirements
- Python 3.10+

### Quick start
```bash
# From repo root
python3 -m agent --request-type campaign_idea --output -
python3 -m agent --request-type performance_review --output -
python3 -m agent --request-type promo_optimization --output -
python3 -m agent --request-type content_creation \
  --payload '{"offer":"72-Hour Craft Flash: 15% off craft","segment":"craft_connoisseurs","product":"Craft Beer"}' \
  --output -
```

The agent defaults to using demo data in `data/demo`. To use your own data, point `--data-dir` at a directory containing:
- `purchases.json` (transactions)
- `customers.json` (profiles)
- `inventory.json` (SKUs)
- `marketing_spend.json`

### Output format
Agent responses are XML-like blocks per the provided PromptRequest spec:
```
<output>
  <summary>...</summary>
  <analysis>...</analysis>
  <recommendation>...</recommendation>
  <metrics>...</metrics>
  <risks>...</risks>
  <next_steps>...</next_steps>
  </output>
```

### Notes
- Guardrails: never discount below cost; protect margin ≥20%; include "Must be 21+" and responsible drinking.
- This is a lightweight, local, no-external-API implementation intended for demonstration and extension.

