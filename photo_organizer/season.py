def get_season(month: int) -> str:
    if month in (3, 4, 5):
        return "wiosna"
    elif month in (6, 7, 8):
        return "lato"
    elif month in (9, 10, 11):
        return "jesień"
    elif month in (12, 1, 2):
        return "zima"
    raise ValueError(f"Invalid month: {month}")
