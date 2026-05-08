# News Features

Milestone 1 now includes experimental macro-news context from the GDELT DOC 2.0 API.

Source:

- GDELT DOC endpoint: `https://api.gdeltproject.org/api/v2/doc/doc`
- Official DOC API documentation: `https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/`

## Query

The current MVP query is intentionally broad:

```text
("stock market" OR "Federal Reserve" OR inflation OR recession OR earnings OR economy)
```

This is not company-specific sentiment. It is market-wide context.

## Generated Features

```text
news_market_article_count
news_market_volume_share
news_market_avg_tone
news_market_tone_abs
news_market_article_count_3d
news_market_volume_share_3d
news_market_avg_tone_3d
news_market_stress
```

## Anti-Lookahead Rule

News features are lagged by one day before being joined to trading rows. A signal generated after today's close sees yesterday's news context, not an unbounded same-day UTC news bucket.

## Cache

Downloaded news data is cached at:

```text
data/news/gdelt_market_news_daily.csv
```

The cache is ignored by git because it is generated data.

## Limitations

- GDELT is a global news index, not a broker-grade financial news feed.
- Tone is an aggregate media tone metric, not a trading signal.
- Macro news features are shared across all symbols.
- Company-specific news, earnings calendars, and event classification belong in later milestones.
