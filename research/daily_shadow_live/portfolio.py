"""Owner-approved active daily universe; historical model protocols remain archived."""
from pathlib import Path
from research.daily_shadow.core import sha
SYMBOLS=('ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX')
PROTOCOL=Path(__file__).resolve().parents[2]/'reports/portfolio-avgo-v1/protocol.txt'
UNIVERSE_REVISION=sha(PROTOCOL.read_bytes())
