---
title: "How to pay with bitcoin"
description: "Make a first bitcoin payment, understand Lightning and on-chain fees, check the destination, and keep the tax record."
template: guide
updated: 2026-10-02
order: 1
attribution: [mempool, coingecko]
understand_first:
  text: "How Bitcoin fees work"
  url: https://fastfactsforsats.com/network/fees-and-the-mempool/
placements:
  - slug: fold
    headline: Fold
    text: "Spend dollars on eligible purchases and receive bitcoin rewards. This earns sats rather than paying the merchant in bitcoin."
sources:
  - name: "mempool.space fee data"
    url: https://mempool.space/docs/api/rest#get-recommended-fees
  - name: "Lightning invoice standard"
    url: https://github.com/lightning/bolts/blob/master/11-payment-encoding.md
  - name: "Lightning Address"
    url: https://lightningaddress.com/
  - name: "BTCPay Server"
    url: https://btcpayserver.org/
  - name: "Phoenix"
    url: https://phoenix.acinq.co/
  - name: "Fold"
    url: https://foldapp.com/
  - name: "IRS"
    url: https://www.irs.gov/filing/digital-assets
---
To pay with bitcoin, open your wallet, scan the seller's payment code, check the details, and approve.

Start with something small. A $5 purchase is [[live:sats-for:5:usd]] at the current price ([[live:when]]).

## Choose the payment method

### Lightning for small everyday payments

Lightning moves payments through a network built on Bitcoin. Payments often arrive in seconds, with low fees. Your wallet may also charge fees for setup, receiving, or managing channels.

Check the wallet's terms and availability before adding money. Examples include [self-custody](/store/how-to-store-sats-safely/) wallets such as Phoenix and custodial services such as Cash App or Strike. Their custody models and regional availability differ.

### On-chain for a direct blockchain transfer

An on-chain payment is recorded in a Bitcoin block. Confirmation takes time, and the fee depends on transaction size and network demand, rather than just the amount sent.

Current estimates are [[live:fee:fast]] for the next block and [[live:fee:slow]] for confirmation within the hour ([[live:when:fees]]). These are estimates, not delivery promises. Your wallet estimates the fee for your actual transaction.

Keep only an amount you are comfortable using in a spending wallet. [How to store sats safely](/store/how-to-store-sats-safely/) covers longer-term storage.

## Make the payment

1. Ask whether the seller accepts Lightning, on-chain bitcoin, or both.
2. Open a compatible wallet and scan the payment code, or copy the payment request from a verified checkout page.
3. Check the amount, destination, network, and fee. Do not approve unfamiliar details.
4. Confirm. A Lightning payment may finish immediately. An on-chain payment remains pending until confirmed.
5. Save the receipt and transaction details.

When paying from a hardware wallet, verify the complete destination and payment details on its own screen.

Some people use a [Lightning address](https://lightningaddress.com/) that looks like an email address. Confirm it with the recipient before paying.

## Where you can spend sats

Some merchants accept bitcoin directly through services such as BTCPay Server. Ask before ordering.

Gift-card services such as Bitrefill can let you buy a store gift card using bitcoin. Check fees, country restrictions, and refund terms. The store then receives the gift card, rather than bitcoin.

A card that spends dollars and earns bitcoin rewards works differently. [How to earn sats](/earn/how-to-earn-sats/) explains those rewards.

## Tips and zaps

On Nostr, a Lightning tip is called a "zap." Stacker News also uses sats for tips. Send a small amount to someone whose work you found useful.

## Keep the tax record

In the US, spending bitcoin is generally a disposal. Compare the sats' cost basis with their dollar value when spent to calculate the gain or loss. Small payments still need records.

Moving older bitcoin into a new wallet does not reset its purchase cost or holding period. [Do I owe taxes on sats?](https://fastfactsforsats.com/rules/taxes-on-sats/) explains the basics.

Try one small payment when you are ready. It is easier to understand the process after you have seen it work.
