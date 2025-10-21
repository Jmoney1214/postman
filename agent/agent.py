from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import json


@dataclass
class Transaction:
    transaction_id: str
    customer_id: str
    sku_id: str
    quantity: int
    revenue: float
    margin: float
    channel: str
    timestamp: datetime


@dataclass
class CustomerProfile:
    customer_id: str
    signup_date: datetime
    total_orders: int
    avg_basket: float
    favorite_categories: List[str]
    channel_preference: str


@dataclass
class InventoryItem:
    sku_id: str
    name: str
    category: str
    cost: float
    price: float
    margin_pct: float
    stock_level: int
    velocity: float


@dataclass
class MarketingSpend:
    channel: str
    campaign_id: str
    daily_spend: float
    impressions: int
    clicks: int
    date: datetime


class LiquorStoreMarketingAgent:
    def __init__(self) -> None:
        self.transactions: list[Transaction] = []
        self.customers: dict[str, CustomerProfile] = {}
        self.inventory: dict[str, InventoryItem] = {}
        self.spend: list[MarketingSpend] = []

    # -------------------------- Data Ingestion --------------------------
    def ingest_data(self, data_dir: Path) -> None:
        data_dir = Path(data_dir)
        self.transactions = self._load_transactions(data_dir / "purchases.json")
        self.customers = {c.customer_id: c for c in self._load_customers(data_dir / "customers.json")}
        self.inventory = {i.sku_id: i for i in self._load_inventory(data_dir / "inventory.json")}
        self.spend = self._load_spend(data_dir / "marketing_spend.json")

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _parse_dt(self, value: str | int | float) -> datetime:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        # Fallback: treat numbers as epoch seconds
        return datetime.utcfromtimestamp(float(value))

    def _load_transactions(self, path: Path) -> list[Transaction]:
        rows = self._load_json(path)
        out: list[Transaction] = []
        for r in rows:
            out.append(
                Transaction(
                    transaction_id=str(r.get("transaction_id")),
                    customer_id=str(r.get("customer_id")),
                    sku_id=str(r.get("sku_id")),
                    quantity=int(r.get("quantity", 1)),
                    revenue=float(r.get("revenue", 0.0)),
                    margin=float(r.get("margin", 0.0)),
                    channel=str(r.get("channel", "unknown")),
                    timestamp=self._parse_dt(r.get("timestamp", datetime.utcnow().isoformat())),
                )
            )
        return out

    def _load_customers(self, path: Path) -> list[CustomerProfile]:
        rows = self._load_json(path)
        out: list[CustomerProfile] = []
        for r in rows:
            out.append(
                CustomerProfile(
                    customer_id=str(r.get("customer_id")),
                    signup_date=self._parse_dt(r.get("signup_date", datetime.utcnow().isoformat())),
                    total_orders=int(r.get("total_orders", 0)),
                    avg_basket=float(r.get("avg_basket", 0.0)),
                    favorite_categories=list(r.get("favorite_categories", [])),
                    channel_preference=str(r.get("channel_preference", "in-store")),
                )
            )
        return out

    def _load_inventory(self, path: Path) -> list[InventoryItem]:
        rows = self._load_json(path)
        out: list[InventoryItem] = []
        for r in rows:
            price = float(r.get("price", 0.0))
            cost = float(r.get("cost", 0.0))
            margin_pct = (price - cost) / price * 100 if price else 0.0
            out.append(
                InventoryItem(
                    sku_id=str(r.get("sku_id")),
                    name=str(r.get("name", "")),
                    category=str(r.get("category", "other")),
                    cost=cost,
                    price=price,
                    margin_pct=float(r.get("margin_pct", margin_pct)),
                    stock_level=int(r.get("stock_level", 0)),
                    velocity=float(r.get("velocity", 0.0)),
                )
            )
        return out

    def _load_spend(self, path: Path) -> list[MarketingSpend]:
        rows = self._load_json(path)
        out: list[MarketingSpend] = []
        for r in rows:
            out.append(
                MarketingSpend(
                    channel=str(r.get("channel")),
                    campaign_id=str(r.get("campaign_id", "")),
                    daily_spend=float(r.get("daily_spend", 0.0)),
                    impressions=int(r.get("impressions", 0)),
                    clicks=int(r.get("clicks", 0)),
                    date=self._parse_dt(r.get("date", datetime.utcnow().isoformat())),
                )
            )
        return out

    # -------------------------- Core Logic --------------------------
    def _rfm_scores(self) -> dict[str, tuple[int, int, float]]:
        now = max((t.timestamp for t in self.transactions), default=datetime.utcnow())
        last_purchase: dict[str, datetime] = {}
        frequency: dict[str, int] = {}
        monetary: dict[str, float] = {}

        for t in self.transactions:
            last_purchase[t.customer_id] = max(last_purchase.get(t.customer_id, t.timestamp), t.timestamp)
            frequency[t.customer_id] = frequency.get(t.customer_id, 0) + 1
            monetary[t.customer_id] = monetary.get(t.customer_id, 0.0) + t.revenue

        scores: dict[str, tuple[int, int, float]] = {}
        for cid in self.customers.keys():
            recency_days = (now - last_purchase.get(cid, now)).days
            freq = frequency.get(cid, 0)
            monetary_value = monetary.get(cid, 0.0)
            scores[cid] = (recency_days, freq, monetary_value)
        return scores

    def run_customer_segmentation(self) -> dict[str, Any]:
        scores = self._rfm_scores()

        segments: dict[str, dict[str, Any]] = {
            "vip": {"members": [], "rules": "R<30d, F>=5, M high", "recommended_tactics": ["VIP exclusives", "early access", "bundles"]},
            "at_risk": {"members": [], "rules": "R>=60d, F>=2", "recommended_tactics": ["win-back email", "limited-time coupon"]},
            "new": {"members": [], "rules": "F=1", "recommended_tactics": ["post-purchase nurture", "welcome loyalty"]},
            "regular": {"members": [], "rules": "F>=2, R<60d", "recommended_tactics": ["category spotlights", "cross-sell"]},
        }

        # Simple bucketing heuristics
        for cid, (recency_days, freq, monetary_value) in scores.items():
            if freq <= 1:
                segments["new"]["members"].append(cid)
            elif recency_days >= 60:
                segments["at_risk"]["members"].append(cid)
            elif freq >= 5 and recency_days < 30 and monetary_value >= 250:
                segments["vip"]["members"].append(cid)
            else:
                segments["regular"]["members"].append(cid)

        # Aggregate stats
        out_defs: list[dict[str, Any]] = []
        for seg_id, seg in segments.items():
            size = len(seg["members"])
            avg_ltv = self._avg_ltv(seg["members"]) if size else 0.0
            churn_risk = 0.2 if seg_id == "vip" else (0.5 if seg_id == "at_risk" else 0.3)
            out_defs.append(
                {
                    "segment_id": seg_id,
                    "size": size,
                    "avg_ltv": round(avg_ltv, 2),
                    "churn_risk": churn_risk,
                    "recommended_tactics": seg["recommended_tactics"],
                }
            )

        return {
            "segment_definitions": out_defs,
            "audience_lists": segments,
        }

    def _avg_ltv(self, customer_ids: Iterable[str]) -> float:
        # Naive LTV proxy: total revenue to date; in real implementation, model future revenue
        revenue_by_customer: dict[str, float] = {}
        for t in self.transactions:
            revenue_by_customer[t.customer_id] = revenue_by_customer.get(t.customer_id, 0.0) + t.revenue
        total = sum(revenue_by_customer.get(cid, 0.0) for cid in customer_ids)
        return total / max(len(list(customer_ids)) or 1, 1)

    def plan_campaigns(self, segments: dict[str, Any]) -> dict[str, Any]:
        # Identify inventory signals
        slow_movers = [i for i in self.inventory.values() if i.velocity < 0.2 and i.stock_level > 10]
        margin_leaders = [i for i in self.inventory.values() if i.margin_pct >= 35]
        seasonal = [i for i in self.inventory.values() if any(k in i.name.lower() for k in ["summer", "holiday", "bbq", "pumpkin"])]

        today = datetime.utcnow().date()
        calendar: list[dict[str, Any]] = []

        def add_campaign(day_offset: int, segment_id: str, offer: str, channel: list[str], budget: float) -> None:
            calendar.append(
                {
                    "date": str(today + timedelta(days=day_offset)),
                    "segment": segment_id,
                    "offer": offer,
                    "channels": channel,
                    "budget": budget,
                }
            )

        # Simple 4-week plan
        add_campaign(1, "new", "Welcome series: 10% off first order", ["email"], 150)
        add_campaign(3, "vip", "VIP exclusive: premium bundle + early access", ["email", "sms"], 300)
        if slow_movers:
            add_campaign(5, "regular", "Clearance: craft beer 15% off (72h)", ["sms", "email"], 250)
        add_campaign(10, "at_risk", "Win-back: $10 off $60+", ["email"], 200)
        add_campaign(14, "regular", "Category spotlight: tequila + pairings", ["social", "email"], 400)

        briefs = [
            {
                "message": "Welcome to our shop — your next favorite bottle awaits.",
                "visuals": "Warm, premium retail feel; diverse customers (21+).",
                "cta": "Shop now",
                "compliance": ["Must be 21+", "Please drink responsibly"],
            },
            {
                "message": "VIP early access to limited releases.",
                "visuals": "Premium product shots, minimal text.",
                "cta": "Unlock access",
                "compliance": ["Must be 21+"],
            },
        ]

        return {
            "campaign_calendar": calendar,
            "creative_briefs": briefs,
            "promo_codes": ["WELCOME10", "VIPACCESS", "CRAFT15", "WINBACK10"],
        }

    def optimize_promo(self) -> dict[str, Any]:
        # Back-of-the-envelope optimizer using margin guardrails and elasticity hints
        recommendations: list[dict[str, Any]] = []

        for item in sorted(self.inventory.values(), key=lambda x: (x.velocity, -x.margin_pct))[:10]:
            if item.price <= 0:
                continue
            base_margin_pct = item.margin_pct
            if base_margin_pct < 20:
                continue  # protect gross margin

            # Try discount depths and compute expected ROI
            candidates: list[tuple[str, float, float]] = []  # (structure, discount_pct, expected_roi)
            for discount_pct in (10, 15, 20):
                new_price = item.price * (1 - discount_pct / 100)
                if new_price <= item.cost:
                    continue  # no below-cost discount
                # Assume simple elasticity: demand_multiplier = 1 + (discount_pct / 25)
                demand_multiplier = 1.0 + (discount_pct / 25.0)
                expected_revenue = new_price * demand_multiplier
                expected_margin_pct = (new_price - item.cost) / new_price * 100
                if expected_margin_pct < 20:
                    continue
                # Proxy ROI: margin dollars vs. no-promo baseline (1 unit)
                baseline_margin = (item.price - item.cost)
                promo_margin = (new_price - item.cost) * demand_multiplier
                expected_roi = (promo_margin - baseline_margin) / max(1.0, (item.price * 0.0 + 1.0))
                candidates.append((f"{discount_pct}% off", discount_pct, expected_roi))

            if not candidates:
                continue
            best = max(candidates, key=lambda c: c[2])
            recommendations.append(
                {
                    "segment": "regular",
                    "sku_id": item.sku_id,
                    "sku_name": item.name,
                    "discount_structure": best[0],
                    "expected_roi": round(best[2], 2),
                    "margin_impact": "guardrail_ok",
                }
            )

        ab_tests = [
            {
                "hypothesis": "15% beats 10% on craft beer with acceptable margin",
                "variants": ["10% off", "15% off", "20% off"],
                "sample_size": 300,
                "success_metrics": ["Incremental margin", "Repeat rate >35%"],
            }
        ]

        return {"promo_recommendations": recommendations, "ab_test_designs": ab_tests}

    def generate_content(self, brief: dict[str, Any]) -> dict[str, Any]:
        offer = brief.get("offer", "")
        segment = brief.get("segment", "all")
        product = brief.get("product", "Featured Favorites")
        compliance = ["Must be 21+", "Please drink responsibly"]

        email_subjects = [
            f"{product} — your next favorite bottle awaits",
            f"{segment.title()} exclusive: {offer}" if offer else f"Exclusive {product} picks",
            "Limited-time offers on top-rated bottles",
            "Unlock new arrivals before they sell out",
            "Weekend specials: curated for you",
        ]
        sms_copy = [
            f"{offer} {product}. Shop now — while supplies last. 21+ Reply STOP to opt out.",
        ]
        social_copy = {
            "short": f"{product}: curated picks, limited time. 21+",
            "mid": f"Level up your bar: {product} on special this week. Shop now — 21+",
            "long": f"Discover {product}. Handpicked selections, limited quantities. Please drink responsibly; 21+ only.",
        }

        email_body_html = (
            "<html><body>"
            f"<h1>{product}</h1>"
            f"<p>{offer}</p>"
            "<a href=\"https://example.com/shop\">Shop now</a>"
            "<footer><small>Must be 21+. Please drink responsibly. Unsubscribe in footer.</small></footer>"
            "</body></html>"
        )

        return {
            "copy_variants": {
                "email_subject_lines": email_subjects,
                "email_body_html": email_body_html,
                "sms_copy": sms_copy,
                "social_ad_copy": social_copy,
            },
            "creative_concepts": [
                {
                    "visual_direction": "Premium product photography, warm tones, minimal text",
                    "mood": "Confident, curated, upscale neighborhood shop",
                }
            ],
            "compliance": compliance,
        }

    def analyze_attribution(self) -> dict[str, Any]:
        # Very simple attribution proxy
        spend_by_channel: dict[str, float] = {}
        revenue_by_channel: dict[str, float] = {}
        for s in self.spend:
            spend_by_channel[s.channel] = spend_by_channel.get(s.channel, 0.0) + s.daily_spend
        for t in self.transactions:
            revenue_by_channel[t.channel] = revenue_by_channel.get(t.channel, 0.0) + t.revenue

        performance: list[dict[str, Any]] = []
        for channel in sorted(set(list(spend_by_channel.keys()) + list(revenue_by_channel.keys()))):
            spend = spend_by_channel.get(channel, 0.0)
            revenue = revenue_by_channel.get(channel, 0.0)
            roas = (revenue / spend) if spend > 0 else None
            performance.append(
                {
                    "channel": channel,
                    "spend": round(spend, 2),
                    "revenue": round(revenue, 2),
                    "roas": round(roas, 2) if roas is not None else None,
                }
            )

        recommendations: list[str] = []
        for p in performance:
            if p["roas"] is not None and p["roas"] >= 3.0:
                recommendations.append(f"Scale {p['channel']} budget by +20% next week")
            elif p["roas"] is not None and p["roas"] < 2.0:
                recommendations.append(f"Pause or reduce {p['channel']} by -30% and test creatives")

        return {
            "channel_performance": performance,
            "budget_reallocation": recommendations,
        }

    def manage_loyalty(self, segments: dict[str, Any]) -> dict[str, Any]:
        rules = {
            "points_program": {"earn": 1, "per_dollar": 1, "burn": {"100_points": "$5"}},
            "tiered_vip": {"tiers": ["silver", "gold", "platinum"], "thresholds": [200, 600, 1200]},
            "referrals": {"give_get": "$10/$10"},
        }
        communications = [
            "Welcome series for new members",
            "Tier-up congratulations and benefits overview",
            "Monthly reward reminder",
        ]
        roi_projection = {
            "expected_ltv_uplift": "+30%",
            "repeat_rate_target": ">50%",
            "net_margin_expectation": "positive after 60 days",
        }
        return {
            "loyalty_rules_engine": rules,
            "member_communications": communications,
            "roi_projections": roi_projection,
        }

    # -------------------------- Request Handling --------------------------
    def handle_request(self, request_type: str, payload: dict[str, Any]) -> str:
        request_type = request_type.strip().lower()

        if request_type == "campaign_idea":
            segments = self.run_customer_segmentation()
            plan = self.plan_campaigns(segments)
            offer = plan["campaign_calendar"][0]["offer"] if plan["campaign_calendar"] else "Limited-time offer"
            output = self._format_output(
                summary=f"Run a targeted campaign: {offer}",
                analysis="Segmentation identifies VIP, new, regular, and at-risk cohorts with distinct tactics. Inventory signals highlight slow movers and margin leaders.",
                recommendation=json.dumps(plan, indent=2),
                metrics=self._expected_metrics_text(),
                risks=self._risks_text(),
                next_steps="1) Approve briefs and promo codes 2) Build segments 3) Launch and monitor",
            )
            return output

        if request_type == "performance_review":
            attribution = self.analyze_attribution()
            output = self._format_output(
                summary="Channel-level ROAS and budget shifts recommended.",
                analysis=json.dumps(attribution, indent=2),
                recommendation="Shift budget toward channels with ROAS ≥ 3.0; pause <2.0.",
                metrics=self._expected_metrics_text(),
                risks=self._risks_text(),
                next_steps="Run weekly review and reallocate budgets accordingly.",
            )
            return output

        if request_type == "promo_optimization":
            promos = self.optimize_promo()
            output = self._format_output(
                summary="Recommended discount structures with guardrails upheld.",
                analysis=json.dumps(promos, indent=2),
                recommendation="Implement top-ROI promos; run AB tests on depth and duration.",
                metrics=self._expected_metrics_text(),
                risks=self._risks_text(),
                next_steps="Create promo codes, set holdouts, launch tests.",
            )
            return output

        if request_type == "content_creation":
            brief = {
                "offer": payload.get("offer", "Weekend Specials"),
                "segment": payload.get("segment", "regular"),
                "product": payload.get("product", "Curated Picks"),
            }
            content = self.generate_content(brief)
            output = self._format_output(
                summary="Copy variants and creative concepts generated with compliance.",
                analysis=json.dumps(content, indent=2),
                recommendation="Use subject lines with urgency and exclusivity; AB test top 2.",
                metrics="CTR +25% vs. benchmark; conversion +15%",
                risks=self._risks_text(),
                next_steps="Select variants, build assets, schedule send.",
            )
            return output

        return self._format_output(
            summary="Unsupported request type",
            analysis=f"Request type '{request_type}' not recognized.",
            recommendation="Use one of: campaign_idea, performance_review, promo_optimization, content_creation",
            metrics="",
            risks="",
            next_steps="",
        )

    # -------------------------- Output Formatting --------------------------
    def _format_output(self, summary: str, analysis: str, recommendation: str, metrics: str, risks: str, next_steps: str) -> str:
        return (
            "<output>\n"
            f"  <summary>{summary}</summary>\n"
            f"  <analysis>{self._escape_xml(analysis)}</analysis>\n"
            f"  <recommendation>{self._escape_xml(recommendation)}</recommendation>\n"
            f"  <metrics>{self._escape_xml(metrics)}</metrics>\n"
            f"  <risks>{self._escape_xml(risks)}</risks>\n"
            f"  <next_steps>{self._escape_xml(next_steps)}</next_steps>\n"
            "</output>"
        )

    def _escape_xml(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _expected_metrics_text(self) -> str:
        return (
            "CAC ≤ $15; LTV ≥ $250; ROAS ≥ 3.0; Email CTR ≥ 4.5%; Retention ≥ 45%; "
            "Promo margin erosion ≤ 8%; Inventory turn +15%"
        )

    def _risks_text(self) -> str:
        return (
            "Compliance and age-gating; margin protection; frequency caps; data privacy (GDPR/CCPA); "
            "promo fatigue; brand equity impact on premium SKUs"
        )
