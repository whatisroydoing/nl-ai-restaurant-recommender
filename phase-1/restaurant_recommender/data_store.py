"""In-memory Restaurant Data Store with filtering by preference."""

from typing import List, Optional

from .models import Preference, RestaurantRecord


class RestaurantDataStore:
    """
    Holds restaurant records and supports filtering by price, location, rating, cuisine.
    """

    def __init__(self, records: Optional[List[RestaurantRecord]] = None):
        self._records: List[RestaurantRecord] = list(records) if records else []

    def load(self, records: List[RestaurantRecord]) -> None:
        """Replace current records with the given list."""
        self._records = list(records)

    def add(self, record: RestaurantRecord) -> None:
        """Append a single record."""
        self._records.append(record)

    def __len__(self) -> int:
        return len(self._records)

    def query(
        self,
        city: Optional[str] = None,
        location: Optional[str] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        min_rating: Optional[float] = None,
        cuisine: Optional[str] = None,
    ) -> List[RestaurantRecord]:
        """
        Return records matching all non-None filters.
        String filters are case-insensitive substring/equality.
        """
        result = []
        for r in self._records:
            if city is not None and (not r.listed_in_city or city.lower() not in r.listed_in_city.lower()):
                continue
            if location is not None and (not r.location or location.lower() not in r.location.lower()):
                continue
            cn = r.cost_numeric
            if price_min is not None and (cn is None or cn < price_min):
                continue
            if price_max is not None and (cn is None or cn > price_max):
                continue
            rn = r.rating_numeric
            if min_rating is not None and (rn is None or rn < min_rating):
                continue
            if cuisine is not None and (not r.cuisines or cuisine.lower() not in r.cuisines.lower()):
                continue
            result.append(r)
        return result

    def query_by_preference(self, pref: Preference) -> List[RestaurantRecord]:
        """Apply a Preference object to filter records."""
        return self.query(
            city=pref.city,
            location=pref.location,
            price_min=pref.price_min,
            price_max=pref.price_max,
            min_rating=pref.min_rating,
            cuisine=pref.cuisine,
        )
