import re

# =========================
# EXTRACT RAM
# =========================

def extract_ram(text):
    match = re.search(r'(\d+)\s?GB', str(text), re.IGNORECASE)
    if match:
        return match.group(1)
    return '8'


# =========================
# EXTRACT PROCESSOR (Apple, Intel, AMD)
# =========================

def extract_processor(text):
    text_lower = str(text).lower()

    # Apple M series
    apple_patterns = [
        (r'm1\s*pro', 'M1 Pro'),
        (r'm1\s*max', 'M1 Max'),
        (r'm1\s*ultra', 'M1 Ultra'),
        (r'm1\b', 'M1'),
        (r'm2\s*pro', 'M2 Pro'),
        (r'm2\s*max', 'M2 Max'),
        (r'm2\s*ultra', 'M2 Ultra'),
        (r'm2\b', 'M2'),
        (r'm3\s*pro', 'M3 Pro'),
        (r'm3\s*max', 'M3 Max'),
        (r'm3\s*ultra', 'M3 Ultra'),
        (r'm3\b', 'M3'),
        (r'm4\s*pro', 'M4 Pro'),
        (r'm4\s*max', 'M4 Max'),
        (r'm4\b', 'M4'),
        (r'apple\s+m\d', 'Apple M-Series')
    ]
    for pattern, name in apple_patterns:
        if re.search(pattern, text_lower):
            return name

    # Intel Core
    intel_patterns = [
        (r'\bi9\b', 'i9'),
        (r'\bi7\b', 'i7'),
        (r'\bi5\b', 'i5'),
        (r'\bi3\b', 'i3'),
        (r'ultra\s*7', 'Ultra 7'),
        (r'ultra\s*5', 'Ultra 5'),
        (r'ultra\s*9', 'Ultra 9')
    ]
    for pattern, name in intel_patterns:
        if re.search(pattern, text_lower):
            return name

    # AMD Ryzen
    amd_patterns = [
        (r'ryzen\s*9', 'Ryzen 9'),
        (r'ryzen\s*7', 'Ryzen 7'),
        (r'ryzen\s*5', 'Ryzen 5'),
        (r'ryzen\s*3', 'Ryzen 3')
    ]
    for pattern, name in amd_patterns:
        if re.search(pattern, text_lower):
            return name

    return 'Unknown'


# =========================
# EXTRACT GPU (Regex fleksibel untuk NVIDIA)
# =========================

def extract_gpu(text):
    text_lower = str(text).lower()

    # 1. Apple GPU
    apple_gpu_patterns = [
        (r'm1\s*pro', 'Apple M1 Pro'),
        (r'm1\s*max', 'Apple M1 Max'),
        (r'm1\s*ultra', 'Apple M1 Ultra'),
        (r'm1\b', 'Apple M1'),
        (r'm2\s*pro', 'Apple M2 Pro'),
        (r'm2\s*max', 'Apple M2 Max'),
        (r'm2\s*ultra', 'Apple M2 Ultra'),
        (r'm2\b', 'Apple M2'),
        (r'm3\s*pro', 'Apple M3 Pro'),
        (r'm3\s*max', 'Apple M3 Max'),
        (r'm3\b', 'Apple M3'),
        (r'm4\s*pro', 'Apple M4 Pro'),
        (r'm4\s*max', 'Apple M4 Max'),
        (r'm4\b', 'Apple M4'),
        (r'apple\s+gpu', 'Apple GPU')
    ]
    for pattern, name in apple_gpu_patterns:
        if re.search(pattern, text_lower):
            return name

    # 2. AMD Radeon
    if re.search(r'radeon', text_lower):
        match = re.search(r'radeon\s*(rx\s*\d{4}|rx\s*\d{3}|vega\s*\d+|pro|hd\s*\d+|graphics)', text_lower)
        if match:
            detail = match.group(1).replace(' ', '').upper()
            return f'AMD Radeon {detail}'
        return 'AMD Radeon'

    # 3. NVIDIA GPU - pendekatan regex (spasi opsional, varian Ti/Super)
    # Pola: (rtx|gtx)\s*(\d{3,4})\s?(ti|super)?
    pattern_nvidia = re.compile(r'\b(rtx|gtx)\s*(\d{3,4})\s?(ti|super)?\b', re.IGNORECASE)
    match = pattern_nvidia.search(text_lower)
    if match:
        series = match.group(1).upper()          # 'RTX' atau 'GTX'
        number = match.group(2)                  # '5070'
        suffix = match.group(3)                  # 'ti' atau 'super' atau None
        if suffix:
            suffix = suffix.capitalize()         # 'Ti' atau 'Super'
            return f'{series} {number} {suffix}'
        else:
            return f'{series} {number}'

    # 4. Intel Arc / Iris Xe / UHD
    if re.search(r'arc\s*a\d{3}', text_lower):
        match = re.search(r'arc\s*(a\d{3})', text_lower)
        if match:
            return f'Intel Arc {match.group(1).upper()}'
        return 'Intel Arc'
    if 'iris xe' in text_lower:
        return 'Iris Xe'
    if 'uhd' in text_lower:
        match = re.search(r'uhd\s*(\d+)', text_lower)
        if match:
            return f'Intel UHD {match.group(1)}'
        return 'Intel UHD'
    if 'hd graphics' in text_lower:
        return 'Intel HD Graphics'

    # 5. Integrated default
    return 'Integrated'