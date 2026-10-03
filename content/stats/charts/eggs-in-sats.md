---
title: A dozen eggs priced in sats
description: See the sats cost of a dozen large eggs since 2011, using BLS monthly averages and bitcoin prices. Learn why both prices matter.
template: chart
question: Did breakfast get cheaper, or did the measuring stick change?
art: hen-two-price-tags
updated: '2026-10-03'
chart:
  slug: eggs-in-sats
  alt: A dozen eggs cost 3,294 sats in August 2026
  source: BLS average price, eggs, grade A, large, per dozen (APU0000708111), blockchain.com, market price (USD)
  source_links:
  - name: BLS average price, eggs, grade A, large, per dozen (APU0000708111)
    url: https://data.bls.gov/timeseries/APU0000708111
  - name: blockchain.com, market price (USD)
    url: https://www.blockchain.com/explorer/charts/market-price
  pulled: October 3, 2026, 15:41 UTC
  data: /data/eggs.json
attribution:
- bls
- blockchain
sources:
- name: BLS average price, eggs, grade A, large, per dozen (APU0000708111)
  url: https://data.bls.gov/timeseries/APU0000708111
- name: blockchain.com, market price (USD)
  url: https://www.blockchain.com/explorer/charts/market-price
---
<!-- auto:start -->
A dozen eggs cost 3,294 sats in August 2026. Each point converts that month's average egg price to sats.

| When | Date | Sats per dozen |
| --- | --- | --- |
| latest | August 2026 | 3,294 sats |
| a year ago | August 2025 | 3,117 sats |
| five years ago | August 2021 | 3,753 sats |
| ten years ago | August 2016 | 251,392 sats |

Download the data behind this chart: [/data/eggs.json](/data/eggs.json). There are 100,000,000 sats in one bitcoin.
<!-- auto:end -->

## What moves this line

This line combines two prices: the dollar price of a dozen eggs and the dollar price of bitcoin. We divide the BLS monthly average egg price by the average bitcoin price for the same month, then multiply by 100,000,000 to get sats.

The sats cost can fall even when eggs cost more dollars. That happens when bitcoin's dollar price rises faster than the price of eggs. It can rise when eggs get more expensive, bitcoin falls, or both.

The logarithmic scale shows equal multiples at equal distances. The table makes the actual amounts easier to compare. These are averages for US cities and a whole month, so your store price and the sats cost today may differ.

A different measuring stick can tell a different story about the same carton. See [Everyday prices in sats](/value/everyday-prices/) for the rest of the basket, or [Bitcoin and inflation](https://fastfactsforsats.com/money/bitcoin-and-inflation/) for the broader explanation.
