from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def size_label(size_gb: float) -> str:
    value = float(size_gb)
    if value < 1:
        mb_value = round(value * 1000)
        if abs(value * 1000 - mb_value) < 1e-9:
            return f"{int(mb_value)}M"
    if value.is_integer():
        return f"{int(value)}g"
    return f"{value:g}g"
