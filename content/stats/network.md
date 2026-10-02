---
title: The Bitcoin network today
description: Hash rate, block height, and the fee it takes to get into the next block, with the live figures and the hash rate chart since 2011.
template: network
nav: true
nav_label: Network
updated: 2026-10-02
attribution: [blockchain, mempool]
sources:
  - name: blockchain.com, total hash rate
    url: https://www.blockchain.com/explorer/charts/hash-rate
  - name: mempool.space, recommended fees and block height
    url: https://mempool.space
---
## What these numbers mean

Hash rate is how much computing power is guessing at the next block, in exahashes (a billion billion guesses) per second. It is the clearest measure of how much work protects the chain, and it has climbed through every price cycle. The figure is a daily estimate, because the true rate can only be inferred from how fast blocks arrive.

Block height is the count of blocks since the first one in January 2009. A new block arrives about every ten minutes, so the height grows by roughly 144 a day.

Fees are what you pay to have a transaction included, priced in sats per virtual byte of transaction size, not per dollar sent. When few people are transacting, the next block costs a few sat/vB; when many are, the price of a quick confirmation rises and patient senders wait for a cheaper block. The three tiers come from mempool.space and refresh every ten minutes. How fees and the mempool work is explained on [Fast Facts for Sats](https://fastfactsforsats.com/network/fees-and-the-mempool/).
