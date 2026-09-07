# Winamax + PulseScore bridge

This project fetches upcoming Winamax events/markets through the PulseScore API and publishes a JSON file that can be read by an external analysis workflow.

## 1. Create a GitHub repository

Create a repository such as `winamax-odds`.

For the simplest integration with ChatGPT/web retrieval, make the repository **public**. The JSON contains betting odds/events, not your PulseScore API key.

## 2. Upload these files

- `fetch_winamax.py`
- `.github/workflows/update.yml`
- `data/winamax_odds.json` (it will be created by the first run)

## 3. Add your secret

GitHub:
Settings → Secrets and variables → Actions → New repository secret

Name:
`PULSESCORE_API_KEY`

Value:
paste your PulseScore key.

Never put the key inside the Python file or committed JSON.

## 4. Run the workflow once

Actions → Update Winamax odds → Run workflow.

After it succeeds, the JSON will be updated every hour.

## 5. Give the analysis workflow the raw JSON URL

For a public repository, the file can be read at:

https://raw.githubusercontent.com/TON_COMPTE/TON_REPO/main/data/winamax_odds.json

Replace `TON_COMPTE/TON_REPO`.

## Important limitation

The free PulseScore plan is 500 requests/month. This script deliberately makes one request per each of the 16 Winamax sports per hourly run, about 384 requests/month. Soccer and other large boards are limited to the first 100 events returned by PulseScore on each run to stay inside the free quota.

If you need exhaustive pagination or more frequent updates, upgrade the PulseScore plan rather than increasing the polling frequency on the free plan.

The script does NOT place bets. It only reads Winamax odds.
