# When building database from API
database_price = api_price * random.uniform(0.70, 0.90)  # 10-30% lower
database_rating = api_rating * random.uniform(0.70, 1.30)  # ±30% change
last_updated = "6 months ago"
```

**This simulates:**
- Database = Your inventory prices and customer satisfaction from 6 months ago
- API = Current market prices and ratings from reviews

---

## **💎 TOP 10 REALISTIC BUSINESS USE CASES**

### **Use Case 1: Repricing Strategy with Quality Correlation** ⭐⭐⭐
**Business Question:** 
*"Market prices have changed in 6 months. Show me which products have increased in price AND improved in rating. These deserve premium pricing. Also flag products with price increases but declining ratings."*

**What This Solves:**
- Smart repricing decisions based on quality changes
- Avoid raising prices on products getting worse reviews
- Justify price increases with quality improvements

**LLM Response Example:**
```
📊 REPRICING RECOMMENDATIONS:

🟢 PREMIUM PRICING JUSTIFIED:
1. "Fjallraven Backpack" (ID: 1)
   6 Months Ago: $83.96, Rating: 3.2★
   Current Market: $109.95 (+31%), Rating: 3.9★ (+22%)
   
   ✅ RECOMMENDATION: Increase to $114.95
   Justification: Quality improved significantly + market supports higher price
   Customer acceptance: HIGH (better product, fair price)

🔴 PRICE INCREASE RISK:
2. "Gold Chain Bracelet" (ID: 5)
   6 Months Ago: $599.00, Rating: 4.2★
   Current Market: $695.00 (+16%), Rating: 3.1★ (-26%)
   
   ⚠️ RECOMMENDATION: Keep at $599 OR decrease to $575
   Justification: Quality declined - customers won't accept higher price
   Risk: High return rate if repriced up
```

**Business Value:** Prevents pricing disasters, maximizes revenue on winners

---

### **Use Case 2: Stock Clearance Priority Matrix** ⭐⭐⭐
**Business Question:**
*"Which products should I put on clearance sale? Prioritize items with declining ratings or where market prices have dropped significantly."*

**What This Solves:**
- Clear out underperforming inventory before it becomes unsellable
- Free up capital for better products
- Avoid holding depreciating assets

**LLM Response Example:**
```
🚨 CLEARANCE PRIORITY LIST:

TIER 1 - URGENT (Rating↓ + Price↓):
1. "SanDisk SSD Plus 1TB" (ID: 9)
   Your Stock Price: $89.99
   Market Price: $109.99
   Your Rating (6mo ago): 4.5★
   Current Rating: 2.7★ (-40%)
   
   🎯 ACTION: Immediate 40% clearance
   Reason: Quality issues emerged (check reviews for defects)
   Target Price: $53.99
   Expected Loss: $36/unit BUT frees capital for better products

TIER 2 - MODERATE (Price↓ significantly):
2. "WD 2TB Elements" (ID: 10)
   Your Price: $52.00
   Market Price: $64.00
   Rating stable at 3.3★
   
   🎯 ACTION: 15% markdown to move faster
   New Price: $44.20
   Still profitable, but market softening
```

**Business Value:** Minimize losses, optimize cash flow

---

### **Use Case 3: Competitive Pricing Intelligence** ⭐⭐⭐
**Business Question:**
*"Compare my prices to current market. Show me where I'm overpriced vs underpriced, and factor in how ratings compare."*

**What This Solves:**
- Find products where you can raise prices (underpriced)
- Identify products needing price cuts to compete
- Use quality as differentiation factor

**LLM Response Example:**
```
💰 PRICING OPPORTUNITIES:

🟢 UNDERPRICED (Raise prices):
1. "White Gold Plated Princess" (ID: 6)
   Your Price: $7.32
   Market Price: $9.99 (+36%)
   Your Rating: 4.1★ vs Market: 3.0★
   
   💡 OPPORTUNITY: Raise to $10.99 (quality premium justified)
   Rationale: You have BETTER ratings than market - charge more!
   Revenue Impact: +$3.67/unit = +50% margin

🔴 OVERPRICED (Need price cut):
2. "Rain Jacket Women" (ID: 15)
   Your Price: $49.99
   Market Price: $39.99 (-20%)
   Your Rating: 2.8★ vs Market: 3.8★
   
   ⚠️ RISK: Overpriced + Lower quality = No sales
   ACTION: Drop to $36.99 or discontinue
```

**Business Value:** Maximize revenue, improve competitiveness

---

### **Use Case 4: Quality Control Alert System** ⭐⭐⭐
**Business Question:**
*"Alert me to any products where ratings have dropped significantly. These might have quality issues or supplier problems."*

**What This Solves:**
- Early warning system for product problems
- Supplier quality monitoring
- Customer satisfaction management

**LLM Response Example:**
```
⚠️ QUALITY ALERT REPORT:

🔴 CRITICAL - Rating Drop >30%:
1. "Mens Casual Slim Fit" (ID: 3)
   6 Months Ago: 4.6★ (Excellent)
   Current: 2.9★ (Poor) - DROP: -37%
   Price: $15.99 → $22.99 (+44%)
   
   🔍 INVESTIGATION NEEDED:
   - Check recent supplier batches
   - Review return reasons
   - Compare materials/construction
   
   💰 FINANCIAL IMPACT:
   - Estimated return rate: 25-30%
   - Reputation damage risk
   - Consider supplier change

🟡 MODERATE - Rating Drop 15-30%:
2. "Opna Women's Short Sleeve" (ID: 18)
   Was: 4.5★ → Now: 3.4★ (-24%)
   
   ACTION: Monitor closely, review customer feedback
```

**Business Value:** Protect brand reputation, reduce returns

---

### **Use Case 5: Market Timing - Buy Low, Sell High** ⭐⭐⭐
**Business Question:**
*"Show me products where market prices have increased significantly but ratings stayed stable or improved. These are my best profit opportunities."*

**What This Solves:**
- Identify products where you can profit from market timing
- Find products bought cheap that can now sell high
- Optimize margin capture

**LLM Response Example:**
```
💎 PROFIT OPPORTUNITY ANALYSIS:

🌟 GOLD TIER (Price↑ + Rating stable/up):
1. "Mens Cotton Jacket" (ID: 2)
   Your Cost (6mo ago): $42.88
   Current Market: $55.99 (+31%)
   Rating: 4.1★ → 4.7★ (+15%)
   
   📈 STRATEGY:
   - You bought low when market was $42.88
   - Market now $55.99 (strong demand + quality improved)
   - Your Selling Price: $49.99 (OLD)
   - NEW Recommended Price: $58.99
   - Margin Improvement: $9.11/unit → $16.11/unit (+77%)
   
   🎯 ACTION: Immediate repricing + feature prominently
   ROI: If you have 20 units, that's +$140 extra profit

2. "Solid Gold Petite Micropave" (ID: 7)
   Your Cost: $56.99
   Market: $168.00 (+195%!)
   Rating: Stable at 3.0★
   
   💰 MASSIVE OPPORTUNITY
```

**Business Value:** Maximize profit margins from market shifts

---

### **Use Case 6: Customer Satisfaction Trend Report** ⭐⭐
**Business Question:**
*"Create a customer satisfaction report. Which products are delighting customers more than 6 months ago? Which are disappointing them?"*

**What This Solves:**
- Understand customer sentiment changes
- Identify product lifecycle stages
- Guide marketing messaging

**LLM Response Example:**
```
😊 CUSTOMER SATISFACTION TRENDS:

🌟 CUSTOMER FAVORITES (Rating improving):
Category: electronics
1. "Acer SB220Q" (ID: 13)
   6mo ago: 2.6★ → Now: 2.9★
   Price: $599 → $599 (stable)
   
   💚 INSIGHT: Product getting better reception over time
   - Possible firmware updates improving performance
   - Word of mouth building
   MARKETING: "Increasingly popular - 4,000+ happy customers"

😟 DECLINING SATISFACTION (Rating dropping):
Category: men's clothing
1. "Mens Casual Premium Slim Fit" (ID: 3)
   6mo ago: 4.6★ → Now: 2.9★ (-37%)
   
   🔴 CUSTOMER COMPLAINT PATTERN:
   - Quality inconsistency
   - Sizing issues
   - Material degradation
   
   ACTION: Pause marketing, fix issues before reputation damage
```

**Business Value:** Protect NPS, guide product decisions

---

### **Use Case 7: Category Performance Dashboard** ⭐⭐
**Business Question:**
*"Compare each product category's price and rating trends. Which categories should I invest more in? Which should I reduce?"*

**What This Solves:**
- Portfolio optimization at category level
- Capital allocation decisions
- Strategic inventory planning

**LLM Response Example:**
```
📊 CATEGORY INTELLIGENCE REPORT:

🏆 WINNING CATEGORIES:
1. JEWELERY
   Avg Price Change: +89%
   Avg Rating Change: +8%
   Products: 4 items
   
   💡 STRATEGIC RECOMMENDATION: EXPAND
   - Strong pricing power
   - Customer satisfaction improving
   - High-margin category
   - Action: Add 3-4 more jewelry SKUs

⚠️ STRUGGLING CATEGORIES:
2. MEN'S CLOTHING
   Avg Price Change: +18%
   Avg Rating Change: -12%
   Products: 4 items
   
   🔍 CONCERN: Price up but quality down
   - Market accepting higher prices
   - But your quality declining
   - Action: Audit suppliers, improve quality or exit
```

**Business Value:** Strategic portfolio management

---

### **Use Case 8: New Product Launch Readiness** ⭐⭐
**Business Question:**
*"I'm considering adding products from the market we don't currently stock. Based on price trends and ratings, which new products are safe bets vs risky?"*

**What This Solves:**
- Reduce new product launch risk
- Data-driven expansion decisions
- Avoid adding problem products

**LLM Response Example:**
```
🆕 NEW PRODUCT EVALUATION:

✅ LOW RISK ADDITIONS:
Products in market but not in your inventory:

1. "USB 3.0 Cable" (Currently not stocked)
   Market Price: $9.99
   Market Rating: 4.3★ (stable/high)
   Category: electronics (you stock 5 others)
   
   💚 RECOMMENDATION: ADD
   - Proven product (high ratings)
   - Complements existing inventory
   - Price point accessible
   - Low return risk (high ratings)

🚨 HIGH RISK - AVOID:
2. "Mystery Fashion Item X" 
   Market Price: $45.99
   Market Rating: 2.1★ (poor)
   
   🔴 WARNING: Don't add
   - Poor customer satisfaction
   - High return probability
   - Brand damage risk
```

**Business Value:** Reduce new product failure rate

---

### **Use Case 9: Price Elasticity Analysis** ⭐⭐⭐
**Business Question:**
*"Show me products where both price AND rating went up together. This indicates customers accept higher prices for quality. Conversely, show products where price increases hurt ratings."*

**What This Solves:**
- Understand customer price sensitivity by product
- Optimize pricing strategy per product
- Avoid pricing mistakes

**LLM Response Example:**
```
🎯 PRICE ELASTICITY INSIGHTS:

💎 PREMIUM PRODUCTS (Price↑ + Rating↑):
These customers PAY MORE for BETTER QUALITY

1. "Fjallraven Backpack" (ID: 1)
   Price: +31% ($83 → $110)
   Rating: +22% (3.2★ → 3.9★)
   
   📈 CUSTOMER BEHAVIOR: Quality-focused
   - Willing to pay premium for improvements
   - Low price sensitivity
   - High brand loyalty
   
   STRATEGY: Premium positioning
   - Can push prices even higher with quality
   - Focus marketing on craftsmanship
   - Target affluent demographics

⚠️ PRICE-SENSITIVE PRODUCTS (Price↑ + Rating↓):
These customers PUNISH price increases

2. "DANVOUY Womens T Shirt" (ID: 20)
   Price: +25%
   Rating: -18%
   
   🔴 CUSTOMER BEHAVIOR: Price-focused
   - High price sensitivity
   - Quality expectations rigid
   - Competitor comparison shopping
   
   STRATEGY: Competitive pricing
   - Match or beat market prices
   - Emphasize value, not premium
   - Volume over margin
```

**Business Value:** Optimize pricing per product segment

---

### **Use Case 10: Vendor Scorecard** ⭐⭐
**Business Question:**
*"Group products by category (as proxy for vendor/supplier). Which categories have improved in both price and quality? Which have declined?"*

**What This Solves:**
- Supplier/vendor performance evaluation
- Sourcing strategy decisions
- Relationship management priorities

**LLM Response Example:**
```
📊 CATEGORY/SUPPLIER PERFORMANCE:

🌟 STAR PERFORMERS:
Category: jewelery (Supplier: Premium Gems Inc.)
- Products: 4 SKUs
- Avg Price Increase: +89%
- Avg Rating Increase: +5%

✅ VERDICT: Excellent partner
- Delivering quality improvements
- Strong pricing power in market
- Renew contracts, negotiate volume discounts
- Consider exclusivity agreement

🚫 UNDERPERFORMERS:
Category: men's clothing (Supplier: Budget Apparel Co.)
- Products: 4 SKUs  
- Avg Price Increase: +22%
- Avg Rating Decrease: -15%

❌ VERDICT: Problem supplier
- Quality declining while prices rising
- Customer dissatisfaction increasing
- ACTION: 
  1. Immediate quality audit meeting
  2. Penalty clauses for defects
  3. Source alternative suppliers
  4. 90-day improvement plan or terminate
