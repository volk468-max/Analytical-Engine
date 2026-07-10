from aae.models.analysis import Observation

class MarketStateEngine:
    def evaluate(self, summary: dict) -> dict:
        trend = summary.get("market_trend", "NO_DATA")
        breadth = summary.get("breadth_proxy", "NO_DATA")
        vix = summary.get("vix")
        quality = float(summary.get("average_quality_score", 0) or 0)

        ts = {"BULLISH":85,"MIXED":55,"BEARISH":25,"NO_DATA":0}.get(trend,40)
        bs = {"BROAD":85,"NEUTRAL":55,"NARROW":25,"NO_DATA":0}.get(breadth,40)
        vs = 40 if vix is None else (85 if float(vix)<=17 else 60 if float(vix)<=25 else 35 if float(vix)<=35 else 10)
        score = round(ts*.40 + bs*.30 + vs*.20 + quality*.10, 1)

        state = "RISK_ON" if score>=75 else "SELECTIVE_RISK_ON" if score>=60 else "NEUTRAL" if score>=45 else "RISK_OFF" if score>=30 else "DEFENSIVE"
        observations = [
            Observation(name="trend", value=str(trend), direction="positive" if ts>=60 else "negative", explanation=f"Trend proxy: {trend}."),
            Observation(name="breadth", value=str(breadth), direction="positive" if bs>=60 else "negative", explanation=f"Breadth proxy: {breadth}."),
            Observation(name="vix", value=str(vix), direction="positive" if vs>=60 else "negative", explanation=f"VIX: {vix}."),
            Observation(name="data_quality", value=str(quality), direction="positive" if quality>=85 else "negative", explanation=f"ADC quality: {quality}."),
        ]
        return {"market_state":state,"market_score":score,"observations":observations}
