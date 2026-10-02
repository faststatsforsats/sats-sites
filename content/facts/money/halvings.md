---
title: Bitcoin halvings explained
description: "Bitcoin's mining reward is cut in half every 210,000 blocks. Learn why halvings happen, what gets cut, and when the next one arrives."
template: guide
updated: 2026-10-02
order: 1
attribution: [mempool]
sources:
  - name: Bitcoin Wiki, Controlled supply
    url: https://en.bitcoin.it/wiki/Controlled_supply
  - name: Bitcoin Core source, GetBlockSubsidy in validation.cpp
    url: https://github.com/bitcoin/bitcoin/blob/master/src/validation.cpp
  - name: mempool.space, block height (the live figure on this page)
    url: https://mempool.space
  - name: Fast Stats for Sats, bitcoin price in dollars since 2011 (halvings marked)
    url: https://faststatsforsats.com/charts/price-usd/
---
A Bitcoin halving cuts the number of new bitcoin paid to miners in half.

It happens every:

210,000 blocks

That works out to roughly once every four years.

The next halving happens at block 1,050,000.

The network is currently at block [[live:height]] ([[live:when:fees]]), leaving [[live:to-halving]] blocks.

At the usual pace, that puts the next halving in 2028.

## What actually gets cut in half?

Every Bitcoin block can create a certain amount of new bitcoin.

That payment is called the block subsidy.

It started at:

50 BTC per block

Then:

| Halving | Block | Subsidy after |
| --- | --- | --- |
| 2012 | 210,000 | 25 BTC |
| 2016 | 420,000 | 12.5 BTC |
| 2020 | 630,000 | 6.25 BTC |
| 2024 | 840,000 | 3.125 BTC |
| Next | 1,050,000 | 1.5625 BTC |

And the process keeps going.

## Why do halvings exist?

Because this is how Bitcoin limits its supply.

Start with 50 bitcoin per block.

Cut that amount in half every 210,000 blocks.

Keep going.

Eventually the new supply approaches zero.

That is the math behind Bitcoin's roughly [21 million coin limit](/money/the-21-million-cap/).

## Why isn't the next halving date exact?

Bitcoin does not schedule halvings by calendar date.

It schedules them by block number.

Blocks average roughly ten minutes apart, but some arrive faster and some slower.

So we know exactly which block causes the halving, but not the exact date far in advance.

## What happens to miners?

Their new-coin revenue per block gets cut in half overnight.

Their electric bill does not.

Less-efficient mining machines may become unprofitable.

Over time, Bitcoin's difficulty adjustment helps keep blocks arriving at roughly the normal pace. The [hash rate chart](https://faststatsforsats.com/charts/hashrate/) on Fast Stats has every halving marked, so you can see each dip and recovery.

## Does a halving push the price up?

No.

A halving changes new supply.

The market decides the price.

Previous halvings happened before major bitcoin [price increases](https://faststatsforsats.com/charts/price-usd/), but history is not a contract with the future.

The halving changes the supply equation. It does not write tomorrow's price tag.
