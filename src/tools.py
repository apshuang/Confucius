import re

def time_string_to_seconds(time_str: str) -> int:
    pattern = re.compile(r'(?:(\d+)m)?(?:(\d+)s)?')
    match = pattern.fullmatch(time_str.strip())
    if not match:
        raise ValueError(f"无效的时间格式: {time_str}")
    minutes = int(match.group(1)) if match.group(1) else 0
    seconds = int(match.group(2)) if match.group(2) else 0
    return minutes * 60 + seconds

def seconds_to_time_string(seconds_int: int) -> str:
    minutes = seconds_int // 60
    seconds = seconds_int % 60
    time_str = ""
    if minutes:
        time_str += f"{minutes}m"
    if seconds:
        time_str += f"{seconds}s"
    return time_str if time_str else "0s"
