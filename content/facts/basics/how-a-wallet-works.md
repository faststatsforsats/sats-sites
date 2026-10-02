---
title: "How a bitcoin wallet works"
description: "A bitcoin wallet manages the keys that let you spend bitcoin. Understand addresses, recovery backups, and the difference between custody options."
template: guide
updated: 2026-10-02
order: 5
attribution: [coingecko]
sources:
  - name: "BIP 39"
    url: https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki
  - name: "BIP 32"
    url: https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
  - name: "Trezor backup formats"
    url: https://trezor.io/guides/backups-recovery/general-standards/single-share-backup-on-trezor
  - name: "Bitcoin Wiki"
    url: https://en.bitcoin.it/wiki/Private_key
  - name: "Fast Acts for Sats"
    url: https://fastactsforsats.com/store/how-to-store-sats-safely/
---
A bitcoin wallet manages your keys. The bitcoin itself is recorded on the blockchain.

Think of the wallet as the key ring that lets you use what is yours.

Sats are the smallest unit of bitcoin. There are 100,000,000 in one bitcoin. Your wallet shows a balance in bitcoin, sats, or dollars, depending on its settings.

## Three things to understand

### Private keys authorize spending

A private key is a secret number used to sign a transaction. Whoever can use the necessary keys can authorize a payment. Keep them secret.

### Addresses receive payments

A bitcoin address tells someone where to send a payment. Many modern addresses begin with bc1; others begin with 1 or 3.

You can share a receiving address, but it can reveal transaction information. It is not a secret key and cannot restore your wallet.

### Backups restore access

Many wallets give you recovery words, often called a seed phrase. They let compatible software or hardware recreate the keys.

Backup formats differ. Many use 12 or 24 words; some newer Trezor backups use 20. Some arrangements also require a passphrase or multiple backup shares. Record exactly what your wallet requires and keep its recovery instructions.

## If the device is lost

With a valid backup and any required passphrase, you can restore access using a compatible wallet and its official recovery process.

Without a working wallet or the required backup, the bitcoin can become permanently inaccessible. There is no central password-reset desk.

For hardware wallets, use the maker's secure recovery procedure. Never type their recovery words into an ordinary website or phone app.

## Hot and cold wallets

A hot wallet keeps keys on an online device, such as a phone. It is convenient for everyday use.

A hardware wallet keeps keys protected inside a separate device and signs transactions there. The connected computer or phone passes information back and forth. It may use a cable, Bluetooth, or QR codes without exposing the keys to the host during normal use.

Some people keep small spending amounts on a phone and longer-term holdings on hardware. Both need a recovery plan.

## Who holds the keys

With a custodial account, the company holds the keys. You have a login and depend on its withdrawal rules and security.

With [self-custody](https://fastactsforsats.com/store/how-to-store-sats-safely/), you control the keys. You also carry the responsibility for backups, address checks, and safe signing.

## What happens when you send bitcoin

Your wallet prepares a transaction, signs it with the required keys, and sends it to the network. If you send 50,000 sats, that is [[live:money-for:50000]] at today's price.

Bitcoin nodes check the transaction. A miner can include it in a block, adding a confirmation. The ledger records which amounts can now be spent under the recipient's keys. [How Bitcoin fees work](/network/fees-and-the-mempool/) explains the fee.

You do not need to understand every part before using a wallet. You do need to protect the keys and prove the backup works. [How to store sats safely](https://fastactsforsats.com/store/how-to-store-sats-safely/) is the next step.
