from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.services.market_data_service import MarketDataService
from app.services.model_service import ModelService


def main():
    db = SessionLocal()
    try:
        market_service = MarketDataService()
        model_service = ModelService()
        history = market_service.load_history(db)
        if len(history) < 40:
            print("Historical market data is insufficient; fetching Alpha Vantage backfill...")
            market_service.fetch_historical_data(db, sync_type="training-bootstrap")
        else:
            print(f"Using {len(history)} existing market rows from MySQL.")
        model_path = model_service.train(db)
        print(f"Model trained and saved to {model_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
