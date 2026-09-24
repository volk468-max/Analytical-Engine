@app.get("/company/market-regime")
async def market_regime():
    adc = ADCConnector(get_adc_url())

    symbols = [
        "NVDA",
        "AMD",
        "AVGO",
        "TSM",
        "ASML",
        "AMAT",
        "LRCX",
        "KLAC",
        "MU",
        "MRVL",
        "VRT",
        "ETN",
        "ANET",
        "CRWV",
        "SNOW",
        "PLTR",
        "META",
        "AMZN",
        "GOOGL",
        "MSFT",
        "TSLA",
        "WIX",
        "ARM",
        "ORCL",
        "GEV",
        "NBIS", 
        "GS",
        "GOOG",
        "CRWD",
        "SMSN.IL",
    ]

    try:
        market_summary = await adc.market_summary()

        spy_history, qqq_history = await asyncio.gather(
            adc.history("SPY", limit=250),
            adc.history("QQQ", limit=250),
        )

        history_results = await asyncio.gather(
            *[
                adc.history(symbol, limit=250)
                for symbol in symbols
            ],
            return_exceptions=True,
        )

        portfolio_histories = {}

        for symbol, result in zip(
            symbols,
            history_results,
        ):
            if isinstance(result, Exception):
                continue

            portfolio_histories[symbol] = result

        engine = MarketRegimeEngine()

        return engine.evaluate(
            market_summary=market_summary,
            spy_history=spy_history,
            qqq_history=qqq_history,
            portfolio_histories=portfolio_histories,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Market regime analysis failed: {exc}",
        )
