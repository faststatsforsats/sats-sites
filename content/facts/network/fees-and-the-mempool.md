---
title: How Bitcoin fees work
description: "Bitcoin fees are based on transaction size, not the amount sent. Learn what sat/vB means, how the mempool works, and why fees rise and fall."
template: guide
updated: 2026-10-02
order: 1
attribution: [mempool]
sources:
  - name: mempool.space, recommended fees (the live figures on this page)
    url: https://mempool.space/docs/api/rest#get-recommended-fees
  - name: Bitcoin Optech, Replace-by-Fee
    url: https://bitcoinops.org/en/topics/replace-by-fee/
  - name: Bitcoin Optech, Child Pays For Parent
    url: https://bitcoinops.org/en/topics/cpfp/
  - name: BIP 141, Segregated Witness (block weight and virtual size)
    url: https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki
---
Bitcoin fees are not based on how much money you send.

They are based mostly on how much space your transaction uses.

That price is measured in:

sats per virtual byte, or sat/vB

Right now, getting into the next block costs about [[live:fee:fast]], while a confirmation within about an hour is around [[live:fee:slow]].

The blockchain is currently at block [[live:height]] ([[live:when:fees]]). The [network page](https://faststatsforsats.com/network/) on Fast Stats shows these figures alongside the hash rate.

## Why do Bitcoin transactions have fees?

Bitcoin blocks have limited space.

Roughly every ten minutes, miners choose transactions and place them into the next block.

When more people want block space than is available, they compete by offering higher fees.

Think of it like priority shipping.

Want it there faster?

You may pay more.

Willing to wait?

You may pay less.

## The mempool

Before a Bitcoin transaction is confirmed, it waits in what is called the mempool.

Think of the mempool as Bitcoin's waiting room.

Transactions offering higher fee rates are usually selected first.

Transactions offering lower fees wait longer when the network is busy.

## Sending $5 can cost the same as sending $5 million

This surprises people.

Bitcoin fees depend on the digital size of the transaction, not its dollar value.

A simple transaction might be around 140 virtual bytes.

At 3 sat/vB:

140 × 3 = about 420 sats

Whether that transaction moves $5 or $5 million does not matter much to the fee.

## Why fees sometimes spike

Demand for block space changes.

Fees can jump during:

- Heavy market activity
- Large exchange withdrawals
- Sudden bursts of network use
- New applications using Bitcoin block space

When the crowd shows up, seats get expensive.

## How people lower fees

Three common approaches are:

**Wait.** Fees can fall dramatically when the network becomes quieter.

**Batch transactions.** Several payments can sometimes be combined into one transaction.

**Use Lightning.** Lightning allows many smaller Bitcoin payments to happen without placing every payment directly onto the blockchain.

Bitcoin block space is scarce.

That is why it has a price. Fees matter more with every [halving](/money/halvings/), because the new coins each block pays out keep shrinking, and the [hash rate chart](https://faststatsforsats.com/charts/hashrate/) on Fast Stats shows the computing power those fees and subsidies pay for.
