# Winamax + PulseScore bridge V2

One sport is refreshed every 2 hours. This uses about 360 API requests/month,
below PulseScore BASIC's 500-request monthly allowance. The cache preserves
previous successful snapshots for the other sports and records the last
refresh time per sport. API key stays in the GitHub Actions secret.
