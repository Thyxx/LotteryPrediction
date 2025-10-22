from __future__ import annotations

from app.database import get_session
from app.data_fetcher import FetchError, update_all_draws


def main() -> None:
    session = get_session()
    try:
        try:
            results = update_all_draws(session)
        except FetchError as exc:
            raise SystemExit(str(exc))
    finally:
        session.close()
    print(
        "Mise à jour terminée: "
        f"{results['loto']} nouveaux tirages Loto, "
        f"{results['euromillions']} nouveaux tirages EuroMillions."
    )


if __name__ == "__main__":
    main()
