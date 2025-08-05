from datetime import datetime

def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
