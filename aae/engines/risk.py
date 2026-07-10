class RiskEngine:
    def evaluate(self, summary: dict, knowledge: list[dict], market_score: float) -> dict:
        vix = summary.get("vix")
        vix_risk = 50 if vix is None else (20 if float(vix)<=17 else 40 if float(vix)<=25 else 70 if float(vix)<=35 else 90)
        breadth_risk = {"BROAD":20,"NEUTRAL":50,"NARROW":80,"NO_DATA":65}.get(summary.get("breadth_proxy","NO_DATA"),60)
        event_scores = [float(x.get("importance_score",0) or 0) for x in knowledge]
        event_risk = min(100, sum(event_scores[:5])/5) if event_scores else 25
        score = round(vix_risk*.4 + breadth_risk*.25 + (100-market_score)*.2 + event_risk*.15,1)
        level = "EXTREME" if score>=75 else "HIGH" if score>=60 else "MODERATE" if score>=40 else "LOW"
        return {"risk_score":score,"risk_level":level}
