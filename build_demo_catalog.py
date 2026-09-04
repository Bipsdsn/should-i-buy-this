"""M1 — build mvp/demo_catalog.json.

8 curated Myntra-style apparel items. Reviews are REALISTIC DEMO DATA authored to mirror the
friction themes mined in the discovery engine + 1E (runs-small, thin/sheer fabric, colour-vs-photo,
occasion doubt, sparse reviews) — NOT scraped real customers (Myntra PDPs are bot-blocked; scraping
review photos raises privacy/rights issues, v3 §2.4). Edge cases are deliberately staged so the
honest `uncertain` / `insufficient_reviews` verdict is demonstrable.

Run:  python build_demo_catalog.py   ->   writes demo_catalog.json
"""
from __future__ import annotations
import json
import os

R = lambda text, rating: {"text": text, "rating": rating}  # noqa: E731

CATALOG = [
    # 1) KURTA — scenario: RUNS SMALL (strong, consistent fit signal)
    {
        "id": "demo-kurta-anouk-01",
        "title": "Yoke Design Straight Kurta",
        "brand": "Anouk",
        "category": "kurta (women)",
        "size_chart": {"S": {"bust_in": 36}, "M": {"bust_in": 38}, "L": {"bust_in": 40},
                       "XL": {"bust_in": 42}, "XXL": {"bust_in": 44}},
        "details": "Viscose rayon straight kurta, calf length, three-quarter sleeves, round neck.",
        "scenario": "runs_small",
        "reviews": [
            R("Runs small. I usually wear M and the M was tight across the bust — size up.", 3),
            R("Ordered my usual L, fits like an M. Returning for XL.", 2),
            R("Beautiful print but the fit is snug at the shoulders and chest.", 3),
            R("Size up! I'm normally S, the S didn't close comfortably.", 3),
            R("Fabric is soft and light, great for daily office wear.", 5),
            R("Length is perfect for me (5'4\"), hits mid-calf.", 4),
            R("Colour is slightly lighter than the photo but still pretty.", 4),
            R("Good quality rayon, didn't fade after two washes.", 5),
            R("The M is tighter than other Anouk kurtas I own, they've changed the fit.", 2),
            R("Sleeves are a bit narrow if you have fuller arms.", 3),
            R("Value for money, but definitely order one size bigger.", 4),
            R("Perfect fit for me — I sized up from M to L as reviews suggested.", 5),
            R("Bust area runs small, rest is fine.", 3),
            R("Loved it, comfortable and true to the pictures except sizing.", 4),
            R("Stitching came slightly loose at the hem within a week.", 2),
            R("I have broad shoulders and the L was still tight up top.", 2),
            R("Lightweight, doesn't cling, good for summer.", 5),
        ],
        "rating": 3.5, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 2) JEANS — scenario: CONFLICTING fit reviews (thigh vs waist)
    {
        "id": "demo-jeans-roadster-02",
        "title": "Slim Fit Mid-Rise Clean Look Jeans",
        "brand": "Roadster",
        "category": "jeans (men)",
        "size_chart": {"30": {"waist_in": 30}, "32": {"waist_in": 32}, "34": {"waist_in": 34},
                       "36": {"waist_in": 36}, "38": {"waist_in": 38}},
        "details": "Slim fit, mid-rise, stretchable cotton, clean look, 5-pocket.",
        "scenario": "conflicting_fit",
        "reviews": [
            R("True to size at the waist, but tight around the thighs — slim fit is really slim.", 3),
            R("Perfect fit, my usual 32 fit exactly right.", 5),
            R("Waist was loose, thighs were snug. Odd fit for athletic legs.", 2),
            R("Great stretch, comfortable all day.", 5),
            R("Runs a bit large at waist, had to use a belt.", 3),
            R("Fabric quality is decent for the price.", 4),
            R("Length was long for me (5'6\"), needed altering.", 3),
            R("Colour fades slightly after a few washes.", 3),
            R("If you have muscular thighs, size up.", 2),
            R("Exactly like the picture, happy with it.", 5),
            R("Not enough stretch as claimed, felt stiff initially.", 3),
            R("Good everyday jeans, waist true to size.", 4),
            R("Thigh area too tight, otherwise fine.", 2),
            R("Comfortable, holds shape well.", 4),
            R("Second pair I've bought, consistent fit for me.", 5),
        ],
        "rating": 3.6, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 3) OVERSIZED SHIRT — scenario: LOOK / styling uncertainty (fabric fine)
    {
        "id": "demo-shirt-herenow-03",
        "title": "Oversized Cotton Casual Shirt",
        "brand": "HERE&NOW",
        "category": "shirt (men)",
        "size_chart": {"S": {"chest_in": 40}, "M": {"chest_in": 42}, "L": {"chest_in": 44},
                       "XL": {"chest_in": 46}},
        "details": "Oversized fit, pure cotton, spread collar, drop shoulder, half sleeves.",
        "scenario": "look_uncertainty",
        "reviews": [
            R("Oversized is genuinely oversized — if you want a normal fit, size down.", 3),
            R("Looks great if you're going for the baggy streetwear look.", 5),
            R("Not sure it suited my body type, I'm slim and it looked like a tent.", 2),
            R("Fabric is thick and premium feeling.", 5),
            R("Perfect drop-shoulder look, exactly like the model.", 5),
            R("Too boxy for me, returned it.", 2),
            R("Great for layering, pairs well with slim jeans.", 4),
            R("Colour is accurate to the photo.", 4),
            R("If you're on the shorter side, oversized can overwhelm your frame.", 3),
            R("Comfortable and breathable cotton.", 5),
            R("Looks stylish with the sleeves rolled.", 4),
            R("Quality is good but the fit is a personal choice — try before deciding.", 3),
            R("I'm 6ft and it looked intentional and cool.", 5),
            R("Wasn't sure how to style it, ended up not wearing it much.", 2),
        ],
        "rating": 3.8, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 4) ANARKALI SET — scenario: OCCASION doubt + quality-vs-price
    {
        "id": "demo-anarkali-libas-04",
        "title": "Floral Print Anarkali Kurta with Dupatta",
        "brand": "Libas",
        "category": "ethnic set (women)",
        "size_chart": {"S": {"bust_in": 36}, "M": {"bust_in": 38}, "L": {"bust_in": 40},
                       "XL": {"bust_in": 42}},
        "details": "Floor-length Anarkali, printed, with dupatta, for festive/occasion wear.",
        "scenario": "occasion_quality",
        "reviews": [
            R("Wore it to a wedding, got so many compliments!", 5),
            R("For the price the fabric feels a bit cheap up close.", 3),
            R("The dupatta material is thinner than expected.", 2),
            R("Flare is beautiful, twirls nicely.", 5),
            R("Colour in real life is a shade duller than the photo.", 3),
            R("Perfect for festive occasions, looks rich in photos.", 4),
            R("Stitching around the yoke was slightly uneven.", 2),
            R("True to size, ordered M and it fit well.", 4),
            R("Length was long, needed hemming (I'm 5'2\").", 3),
            R("Great festive buy, comfortable to wear all evening.", 5),
            R("Not sure it's worth it for a one-time wedding wear, quality is average.", 3),
            R("Loved the print, elegant for pujas and functions.", 5),
            R("Lining is a bit scratchy, wore an inner.", 3),
            R("Looks more expensive than it is — good for occasions.", 4),
            R("Dupatta colour didn't exactly match the kurta.", 2),
            R("Fit is true to size but size up if you want it loose for dancing.", 4),
        ],
        "rating": 3.6, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 5) MIDI DRESS — scenario: IMAGE vs REALITY (colour + length)
    {
        "id": "demo-dress-sangria-05",
        "title": "Floral Print Fit & Flare Midi Dress",
        "brand": "SANGRIA",
        "category": "dress (women)",
        "size_chart": {"XS": {"bust_in": 32, "waist_in": 26}, "S": {"bust_in": 34, "waist_in": 28},
                       "M": {"bust_in": 36, "waist_in": 30}, "L": {"bust_in": 38, "waist_in": 32}},
        "details": "Fit-and-flare midi, floral print, short sleeves, concealed zip.",
        "scenario": "image_vs_reality",
        "reviews": [
            R("Colour is noticeably lighter/washed out compared to the website photo.", 2),
            R("Shorter than 'midi' — hits above the knee on me (5'5\").", 2),
            R("Print is pretty but the background is more beige than white in reality.", 3),
            R("Fit is true to size, waist defined nicely.", 4),
            R("Fabric is a bit see-through in bright light, wore a slip.", 2),
            R("Loved it, flattering flare.", 5),
            R("The real product looks cheaper than the styled photo.", 2),
            R("Comfortable and good for brunch outings.", 4),
            R("Length is fine if you're petite.", 3),
            R("Zip quality feels flimsy.", 2),
            R("Colour accurate on my screen actually, happy.", 4),
            R("Sleeves are a little tight on the arms.", 3),
            R("Nice for the price if you manage expectations on colour.", 3),
            R("Ordered S, fit perfectly, but the shade is different.", 3),
        ],
        "rating": 2.9, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 6) SHOES — scenario: RUNS SMALL (footwear, half-size)
    {
        "id": "demo-shoes-puma-06",
        "title": "Running Shoes",
        "brand": "Puma",
        "category": "footwear (unisex)",
        "size_chart": {"UK6": {"foot_cm": 24.5}, "UK7": {"foot_cm": 25.5}, "UK8": {"foot_cm": 26.5},
                       "UK9": {"foot_cm": 27.5}, "UK10": {"foot_cm": 28.5}},
        "details": "Lightweight running shoes, mesh upper, cushioned sole.",
        "scenario": "runs_small",
        "reviews": [
            R("Run small — order half a size up. My UK8 felt like a 7.5.", 3),
            R("Tight in the toe box, went up a size and it was perfect.", 3),
            R("Very comfortable once I sized up.", 5),
            R("True to size for me, no issues.", 4),
            R("Narrow fit, not great for wide feet.", 2),
            R("Great cushioning for daily runs.", 5),
            R("Ordered my usual size and had to return — too tight.", 2),
            R("Lightweight and breathable.", 5),
            R("Looks exactly like the pictures.", 4),
            R("Size up if you wear thick socks.", 3),
            R("Sole started wearing after a month of heavy use.", 3),
            R("Comfortable, but definitely runs small.", 4),
            R("Perfect for gym and walking.", 5),
            R("Half size up is the way to go.", 4),
        ],
        "rating": 3.7, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 7) BODYCON DRESS — scenario: QUALITY (sheer fabric) + body-fit anxiety
    {
        "id": "demo-bodycon-mastharbour-07",
        "title": "Ribbed Bodycon Mini Dress",
        "brand": "Mast & Harbour",
        "category": "dress (women)",
        "size_chart": {"XS": {"bust_in": 31, "waist_in": 24}, "S": {"bust_in": 33, "waist_in": 26},
                       "M": {"bust_in": 35, "waist_in": 28}, "L": {"bust_in": 37, "waist_in": 30}},
        "details": "Ribbed stretch bodycon, mini length, sleeveless.",
        "scenario": "quality_sheer",
        "reviews": [
            R("The fabric is thin and slightly see-through, be careful with innerwear.", 2),
            R("Clings to every curve — flattering but not forgiving.", 3),
            R("Ribbed material is stretchy and comfortable.", 4),
            R("Sheer in bright light, disappointed for the price.", 2),
            R("True to size, hugs nicely.", 4),
            R("Shows every line, needs seamless innerwear.", 3),
            R("Loved the fit, very body-hugging as expected.", 5),
            R("Material feels cheap and thin.", 2),
            R("Great for a night out if you're confident.", 5),
            R("Length is very short (I'm 5'7\").", 3),
            R("Stretchy but the seams show through.", 2),
            R("Perfect bodycon, just size up if you want less clingy.", 4),
            R("Not sure it suited my body shape, felt too exposing.", 2),
            R("Colour accurate, fit accurate, only the sheerness bothered me.", 3),
        ],
        "rating": 3.0, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
    # 8) TRAINING TEE — scenario: SPARSE REVIEWS (forces honest 'insufficient_reviews')
    {
        "id": "demo-tee-hrx-08",
        "title": "Rapid-Dry Training T-Shirt",
        "brand": "HRX",
        "category": "activewear (men)",
        "size_chart": {"S": {"chest_in": 38}, "M": {"chest_in": 40}, "L": {"chest_in": 42},
                       "XL": {"chest_in": 44}},
        "details": "Rapid-dry training tee, slim athletic fit, moisture-wicking.",
        "scenario": "sparse_reviews",
        "reviews": [
            R("Fits well, good for workouts.", 4),
            R("Decent quality, dries fast.", 4),
        ],
        "rating": 4.0, "image_url": "", "illustrative_photos": [], "source": "demo",
    },
]


def main() -> None:
    out = os.path.join(os.path.dirname(__file__), "demo_catalog.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(CATALOG, f, ensure_ascii=False, indent=2)

    # M1 done-criteria: loads + edge cases present
    scenarios = {i["scenario"] for i in CATALOG}
    n_reviews = {i["id"]: len(i["reviews"]) for i in CATALOG}
    sparse = [k for k, v in n_reviews.items() if v <= 3]
    assert len(CATALOG) >= 6, "need >=6 items"
    for need in ("runs_small", "conflicting_fit", "sparse_reviews", "image_vs_reality"):
        assert need in scenarios, f"missing edge case: {need}"
    print(f"Wrote {out}")
    print(f"Items: {len(CATALOG)} | reviews total: {sum(n_reviews.values())} "
          f"(min {min(n_reviews.values())}, max {max(n_reviews.values())})")
    print(f"Scenarios: {sorted(scenarios)}")
    print(f"Sparse-review item(s) for honesty demo: {sparse}")


if __name__ == "__main__":
    main()
