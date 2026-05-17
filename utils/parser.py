import re

# =====================================================
# 1. EXTRACT RAM (🎯 FIX MUTLAK: Kebal VRAM & Storage)
# =====================================================
def extract_ram(text):
    text_clean = str(text).lower()
    
    # -------------------------------------------------
    # LANGKAH A: PROTEKSI AWAL KATA KUNCI "RAM"
    # -------------------------------------------------
    # Jika pola angka + GB berdekatan langsung dengan teks 'ram', ambil duluan.
    # Ini mengunci angka '32' dari kalimat "... RAM 32GB VGA 2GB ..."
    ram_direct_match = re.search(r'(\d+)\s?gb\s?ram|ram\s?(\d+)\s?gb', text_clean)
    if ram_direct_match:
        return ram_direct_match.group(1) or ram_direct_match.group(2)

    # -------------------------------------------------
    # LANGKAH B: PEMBERSIHAN DATA STORAGE (SSD/HDD)
    # -------------------------------------------------
    # Menghapus kapasitas storage berakhiran GB/TB agar tidak mengacaukan pembacaan
    text_clean = re.sub(r'\d+\s?gb\s?(ssd|nvme|hdd|storage|rom)', '', text_clean)
    text_clean = re.sub(r'(ssd|nvme|hdd|storage|rom)\s?\d+\s?gb', '', text_clean)
    text_clean = re.sub(r'\d+\s?tb\s?(ssd|nvme|hdd|storage|rom)?', '', text_clean)
    
    # -------------------------------------------------
    # LANGKAH C: PEMBERSIHAN VRAM GRAFIS (GPU)
    # -------------------------------------------------
    # Menghapus kapasitas memori kartu grafis menggunakan batas kata tegas (\b)
    gpu_keywords = r'rtx|gtx|quadro|t2000|t1000|vram|nvidia|geforce|radeon|arc|iris'
    text_clean = re.sub(r'\b\d+\s?gb\s?(' + gpu_keywords + r')\b', '', text_clean)
    text_clean = re.sub(r'\b(' + gpu_keywords + r')\s?\d+\s?gb\b', '', text_clean)
    
    # Saring kata ambigu seperti "vga Xgb" secara ketat tanpa melompati baris kata lain
    text_clean = re.sub(r'\bvga\s?\d+\s?gb\b', '', text_clean)
    text_clean = re.sub(r'\bgraphics\s?\d+\s?gb\b', '', text_clean)
    
    # -------------------------------------------------
    # LANGKAH D: EKSTRAKSI & VALIDASI AKHIR
    # -------------------------------------------------
    # Ambil sisa angka berakhiran GB yang lolos dari filter penyaringan di atas
    pattern = re.compile(r'(\d+)\s?GB', re.IGNORECASE)
    matches = [m.group(1) for m in pattern.finditer(text_clean)]
    
    # Filter kesesuaian logika bisnis kapasitas RAM laptop/PC pasaran
    valid_ram_sizes = ['4', '8', '12', '16', '24', '32', '64']
    filtered_matches = [m for m in matches if m in valid_ram_sizes]
    
    if filtered_matches:
        return filtered_matches[0]
    elif matches:
        return matches[0]
    else:
        return '8'  # Fallback standar jika data iklan tidak menuliskan RAM

# =====================================================
# 2. EXTRACT PROCESSOR (Lini Komponen Modern)
# =====================================================
def extract_processor(text):
    text_lower = str(text).lower()

    # Apple M series
    apple_patterns = [
        (r'm1\s*pro', 'M1 Pro'), (r'm1\s*max', 'M1 Max'), (r'm1\s*ultra', 'M1 Ultra'), (r'm1\b', 'M1'),
        (r'm2\s*pro', 'M2 Pro'), (r'm2\s*max', 'M2 Max'), (r'm2\s*ultra', 'M2 Ultra'), (r'm2\b', 'M2'),
        (r'm3\s*pro', 'M3 Pro'), (r'm3\s*max', 'M3 Max'), (r'm3\s*ultra', 'M3 Ultra'), (r'm3\b', 'M3'),
        (r'm4\s*pro', 'M4 Pro'), (r'm4\s*max', 'M4 Max'), (r'm4\b', 'M4'), (r'apple\s+m\d', 'Apple M-Series')
    ]
    for pattern, name in apple_patterns:
        if re.search(pattern, text_lower):
            return name

    # Intel Core (Termasuk Generasi Ultra)
    intel_patterns = [
        (r'\bi9\b', 'i9'), (r'\bi7\b', 'i7'), (r'\bi5\b', 'i5'), (r'\bi3\b', 'i3'),
        (r'\bcore\s*ultra\s*9\b', 'Core Ultra 9'), (r'\bcore\s*ultra\s*7\b', 'Core Ultra 7'), (r'\bcore\s*ultra\s*5\b', 'Core Ultra 5'),
        (r'\bultra\s*9\b', 'Ultra 9'), (r'\bultra\s*7\b', 'Ultra 7'), (r'\bultra\s*5\b', 'Ultra 5'),
        (r'\bcore\s*9\b', 'Core 9'), (r'\bcore\s*7\b', 'Core 7'), (r'\bcore\s*5\b', 'Core 5'), (r'\bcore\s*3\b', 'Core 3')
    ]
    for pattern, name in intel_patterns:
        if re.search(pattern, text_lower):
            return name

    # AMD Ryzen (Termasuk seri AI)
    amd_patterns = [
        (r'ryzen\s+ai\s+9\b', 'Ryzen AI 9'), (r'ryzen\s+ai\s+7\b', 'Ryzen AI 7'), (r'ryzen\s+ai\s+5\b', 'Ryzen AI 5'),
        (r'ryzen\s*9\b', 'Ryzen 9'), (r'ryzen\s*7\b', 'Ryzen 7'), (r'ryzen\s*5\b', 'Ryzen 5'), (r'ryzen\s*3\b', 'Ryzen 3')
    ]
    for pattern, name in amd_patterns:
        if re.search(pattern, text_lower):
            return name

    return 'Unknown'

# =====================================================
# 3. EXTRACT GPU (NVIDIA Quadro, GeForce, Radeon, Intel)
# =====================================================
def extract_gpu(text):
    text_lower = str(text).lower()

    # A. Apple Silicon GPU Integrated
    apple_gpu_patterns = [
        (r'm1\s*pro', 'Apple M1 Pro'), (r'm1\s*max', 'Apple M1 Max'), (r'm1\s*ultra', 'Apple M1 Ultra'), (r'm1\b', 'Apple M1'),
        (r'm2\s*pro', 'Apple M2 Pro'), (r'm2\s*max', 'Apple M2 Max'), (r'm2\s*ultra', 'Apple M2 Ultra'), (r'm2\b', 'Apple M2'),
        (r'm3\s*pro', 'Apple M3 Pro'), (r'm3\s*max', 'Apple M3 Max'), (r'm3\b', 'Apple M3'),
        (r'm4\s*pro', 'Apple M4 Pro'), (r'm4\s*max', 'Apple M4 Max'), (r'm4\b', 'Apple M4'), (r'apple\s+gpu', 'Apple GPU')
    ]
    for pattern, name in apple_gpu_patterns:
        if re.search(pattern, text_lower):
            return name

    # B. NVIDIA Quadro Workstation Series (Mendeteksi seri arsitektur mobile)
    pattern_quadro = re.compile(r'\bquadro\s*([a-zA-Z]?\d{3,4})\b', re.IGNORECASE)
    match_quadro = pattern_quadro.search(text_lower)
    if match_quadro:
        return f"NVIDIA Quadro {match_quadro.group(1).upper()}"
        
    if 'quadro' in text_lower:
        return 'NVIDIA Quadro'

    # C. NVIDIA GeForce (RTX / GTX Seri Diskret)
    pattern_nvidia = re.compile(r'\b(rtx|gtx)\s*(\d{3,4})\s?(ti|super)?\b', re.IGNORECASE)
    match = pattern_nvidia.search(text_lower)
    if match:
        series = match.group(1).upper()
        number = match.group(2)
        suffix = match.group(3)
        gpu_name = f'{series} {number}'
        if suffix:
            gpu_name += f' {suffix.capitalize()}'
        if re.search(r'radeon', text_lower):
            gpu_name += ' + AMD Radeon'
        return gpu_name

    # D. AMD Radeon Graphics
    if re.search(r'radeon', text_lower):
        match = re.search(r'radeon\s*(rx\s*\d{4}|rx\s*\d{3}|vega\s*\d+|pro|hd\s*\d+|graphics)', text_lower)
        if match:
            detail = match.group(1).replace(' ', '').upper()
            return f'AMD Radeon {detail}'
        return 'AMD Radeon'

    # E. Intel Arc / Iris Xe / UHD / HD Graphics
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

    return 'Integrated'