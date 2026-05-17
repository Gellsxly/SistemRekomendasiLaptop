import re

# =========================
# EXTRACT RAM (Improved: skip GPU VRAM)
# =========================
def extract_ram(text):
    text_str = str(text)
    # Cari semua kemunculan angka diikuti GB (case insensitive)
    pattern = re.compile(r'(\d+)\s?GB', re.IGNORECASE)
    matches = list(pattern.finditer(text_str))
    
    # Filter: abaikan jika dalam 30 karakter sebelumnya ada kata yang menandakan GPU
    filtered_matches = []
    for match in matches:
        start = match.start()
        # Ambil teks 30 karakter sebelum match
        before = text_str[max(0, start-30):start].lower()
        # Jika ada keyword GPU, skip
        if any(keyword in before for keyword in ['rtx', 'gtx', 'vram', 'gddr', 'graphics', 'nvidia', 'amd radeon']):
            continue
        filtered_matches.append(match)
    
    if filtered_matches:
        # Ambil nilai yang pertama kali muncul
        return filtered_matches[0].group(1)
    elif matches:
        # Fallback: ambil match pertama
        return matches[0].group(1)
    else:
        return '8'

# =========================
# EXTRACT PROCESSOR (Apple, Intel, AMD including Ryzen AI)
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

    # Intel Core (termasuk Core 3/5/7/9 dan Ultra)
    intel_patterns = [
        (r'\bi9\b', 'i9'),
        (r'\bi7\b', 'i7'),
        (r'\bi5\b', 'i5'),
        (r'\bi3\b', 'i3'),
        (r'\bcore\s*ultra\s*9\b', 'Core Ultra 9'),
        (r'\bcore\s*ultra\s*7\b', 'Core Ultra 7'),
        (r'\bcore\s*ultra\s*5\b', 'Core Ultra 5'),
        (r'\bultra\s*9\b', 'Ultra 9'),
        (r'\bultra\s*7\b', 'Ultra 7'),
        (r'\bultra\s*5\b', 'Ultra 5'),
        (r'\bcore\s*9\b', 'Core 9'),
        (r'\bcore\s*7\b', 'Core 7'),
        (r'\bcore\s*5\b', 'Core 5'),
        (r'\bcore\s*3\b', 'Core 3')
    ]
    for pattern, name in intel_patterns:
        if re.search(pattern, text_lower):
            return name

    # AMD Ryzen (includes Ryzen AI)
    amd_patterns = [
        (r'ryzen\s+ai\s+9\b', 'Ryzen AI 9'),
        (r'ryzen\s+ai\s+7\b', 'Ryzen AI 7'),
        (r'ryzen\s+ai\s+5\b', 'Ryzen AI 5'),
        (r'ryzen\s*9\b', 'Ryzen 9'),
        (r'ryzen\s*7\b', 'Ryzen 7'),
        (r'ryzen\s*5\b', 'Ryzen 5'),
        (r'ryzen\s*3\b', 'Ryzen 3')
    ]
    for pattern, name in amd_patterns:
        if re.search(pattern, text_lower):
            return name

    return 'Unknown'

# =========================
# EXTRACT GPU (prioritas NVIDIA, dual GPU)
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

    # 2. NVIDIA GPU (prioritas utama)
    pattern_nvidia = re.compile(r'\b(rtx|gtx)\s*(\d{3,4})\s?(ti|super)?\b', re.IGNORECASE)
    match = pattern_nvidia.search(text_lower)
    if match:
        series = match.group(1).upper()
        number = match.group(2)
        suffix = match.group(3)
        gpu_name = f'{series} {number}'
        if suffix:
            gpu_name += f' {suffix.capitalize()}'
        # Cek apakah ada juga AMD Radeon (dual GPU)
        if re.search(r'radeon', text_lower):
            gpu_name += ' + AMD Radeon'
        return gpu_name

    # 3. AMD Radeon (jika tidak ada NVIDIA)
    if re.search(r'radeon', text_lower):
        match = re.search(r'radeon\s*(rx\s*\d{4}|rx\s*\d{3}|vega\s*\d+|pro|hd\s*\d+|graphics)', text_lower)
        if match:
            detail = match.group(1).replace(' ', '').upper()
            return f'AMD Radeon {detail}'
        return 'AMD Radeon'

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