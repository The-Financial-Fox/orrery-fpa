# Privacy policy: Orrery for FP&A

Last updated: 27 November 2026

Orrery for FP&A ("Orrery") is a free, open-source Claude plugin published by Christian Martinez. This policy explains what data Orrery handles and where it goes.

## Short version

Orrery has no servers, no accounts, no analytics and no connectors. It sends nothing to the publisher or to anyone else. It works only on the files you give Claude, inside your own Claude session.

## What Orrery reads

Orrery reads only the files you attach or point it to, such as:

- bank statement lines and GL cash lines, which can include customer and supplier names
- journal entries, which can include vendor names and the user names of preparers and approvers
- actuals, budget, sales and forecast history

It does not read your Claude memory, chat history or any other files.

## What Orrery writes

Orrery writes its results as files in your session's working folder, under `orrery-close/` (or `orrery-recon/`, `orrery-screening/` and similar). These files can contain the names that were in your input files, plus the names of reviewers you record in the review queue and close log. To carry out the calculations, Claude writes and runs Python scripts in that same folder. These files stay in your Claude session and are subject to Anthropic's own data and retention policies for your account. You can delete them at any time.

## What Orrery sends

Nothing. Orrery makes no network requests, contains no tracking, and does not send data to the publisher or any third party.

## Retention

The publisher receives and retains no data from Orrery.

## Children

Orrery is a professional finance tool and is not intended for anyone under 18.

## Changes

Changes to this policy are published in this file in the GitHub repository, with the date updated above.

## Contact

Christian Martinez: [christianmartinez-thefinancialfox.com](https://www.christianmartinez-thefinancialfox.com/)
