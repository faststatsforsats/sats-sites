---
title: "How to store sats safely"
description: "Understand exchange accounts, phone wallets, and hardware wallets. Protect your bitcoin with a checked backup and careful transfers."
template: guide
updated: 2026-10-02
order: 1
attribution: [coingecko]
understand_first:
  text: "How a bitcoin wallet works"
  url: https://fastfactsforsats.com/basics/how-a-wallet-works/
placements:
  - slug: trezor
    headline: Trezor
    text: "Hardware wallets with on-device checks and several backup options."
  - slug: bitbox
    headline: BitBox02 Nova
    text: "A hardware wallet with a Bitcoin-only edition and microSD backup. Protect the card as carefully as recovery words."
  - slug: jade
    headline: Blockstream Jade
    text: "Hardware wallets for Bitcoin and Liquid, with QR signing on supported models."
  - slug: ledger
    headline: Ledger
    text: "Hardware wallets supporting bitcoin and other assets. Review supported phones, apps, and backup options."
  - slug: billfodl
    headline: Billfodl
    text: "A metal recovery-word backup. Check compatibility with your backup format before buying."
sources:
  - name: "Trezor"
    url: https://trezor.io/compare
  - name: "BitBox"
    url: https://bitbox.swiss/bitbox02/
  - name: "BitBox backup guide"
    url: https://support.bitbox.swiss/basics/bitbox02-setup-microsd-backup
  - name: "Blockstream Jade"
    url: https://blockstream.com/jade/
  - name: "Ledger"
    url: https://shop.ledger.com/pages/hardware-wallet
  - name: "BIP 39"
    url: https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki
  - name: "Trezor backup formats"
    url: https://trezor.io/guides/backups-recovery/general-standards/single-share-backup-on-trezor
---
Protecting bitcoin means protecting the keys that let you spend it. If you hold your own keys, you also need a backup you can recover from.

100,000 sats are worth [[live:money-for:100000]] at the current price ([[live:when]]). The [sats converter](https://faststatsforsats.com/tools/sats-converter/) checks any other amount.

## Choose where to keep it

- Exchange account: The company holds the keys. Easy to use, but withdrawals depend on the company and its rules.
- Self-custody phone wallet: You hold the keys on your phone. Useful for small amounts, with security that depends on your phone and backup.
- Hardware wallet: A separate device protects the keys and approves transactions. Useful for amounts you want to keep more carefully protected.

There is no universal balance at which you must buy a hardware wallet. Consider the amount, the device cost, and your ability to manage the backup. Self-custody replaces company risk with responsibilities of your own.

## Set it up carefully

1. Buy from the maker or an authorized seller listed by the maker. Check the current models in [best hardware wallets compared](/store/best-hardware-wallets/).
2. Follow the official setup guide. Create your own new wallet and record the backup it generates. Never use words supplied on a pre-filled card.
3. Verify the backup using the maker's procedure before depositing savings. [How to set up a hardware wallet](/store/hardware-wallet-setup/) walks through this.
4. Verify the complete receiving address on the device, then send a small test amount over the correct network. Wait for confirmation before sending more.
5. Protect the backup in a secure place, separate from the device. A second copy in another secure location can protect against loss, but it also needs protection from theft.
6. Leave recovery instructions for someone you trust. Explain where to find the plan without casually revealing your secret words.

## Protect the backup

For a hardware wallet, follow the maker's secure backup and recovery process. Never enter its recovery words into a website, ordinary computer form, or phone app. Never photograph them or put them in email or cloud storage.

Someone with a complete backup can usually spend the bitcoin without your device or PIN. Protect a microSD backup just as carefully as written words.

Paper is vulnerable to fire and water. A suitable metal backup can offer better protection. Match it to your wallet's backup format.

## Avoid the common mistakes

- Keep the backup separate from the device.
- Check the complete address on the trusted device screen. A QR code or copied address still needs checking.
- Use a small test transfer before moving a larger amount.
- Understand an optional passphrase before enabling it. Losing it can make the wallet unrecoverable even if you have the backup words.
- Review your recovery plan periodically. Check the backup's location and follow official guidance for software updates.

A screenshot of a receiving address cannot restore a wallet. An exchange "vault" still relies on the exchange's keys.

The goal is a wallet you can use and a recovery plan that works. A little boring is good here.
