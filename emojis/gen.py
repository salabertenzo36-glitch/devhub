import subprocess, os

OUT = "/Users/epsylon2/:eof/bot/emojis"
SIZE = 128
VIEWBOX = 512

emojis = {}

# ─── MODERATION : bouclier plein, épais, net ───
emojis["moderation"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M256 48 L80 128 L80 260 C80 370 160 450 256 480 C352 450 432 370 432 260 L432 128 Z"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round" stroke-linecap="round"/>
  <polyline points="180,240 230,290 330,190"
            fill="none" stroke="#C0C0C0" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# ─── MOD AVANCÉE : deux épées croisées ───
emojis["mod_avancee"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <line x1="100" y1="400" x2="380" y2="120" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="412" y1="400" x2="132" y2="120" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <rect x="370" y="90" width="60" height="18" rx="4" transform="rotate(-45 400 99)" fill="#C0C0C0"/>
  <rect x="82" y="90" width="60" height="18" rx="4" transform="rotate(45 112 99)" fill="#C0C0C0"/>
  <line x1="80" y1="410" x2="130" y2="410" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
  <line x1="382" y1="410" x2="432" y2="410" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
</svg>'''

# ─── VOCAL : micro propre ───
emojis["vocal"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <rect x="216" y="80" width="80" height="180" rx="40" fill="none" stroke="#C0C0C0" stroke-width="18"/>
  <path d="M160 240 C160 320 200 380 256 380 C312 380 352 320 352 240"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <line x1="256" y1="380" x2="256" y2="430" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <line x1="200" y1="430" x2="312" y2="430" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
</svg>'''

# ─── UTILITAIRES : clé anglaise ───
emojis["utilitaires"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <line x1="120" y1="392" x2="320" y2="192" stroke="#C0C0C0" stroke-width="22" stroke-linecap="round"/>
  <circle cx="350" cy="162" r="58" fill="none" stroke="#C0C0C0" stroke-width="18"/>
  <circle cx="350" cy="162" r="26" fill="#0a0a0a" stroke="#C0C0C0" stroke-width="14"/>
  <rect x="80" y="370" width="60" height="50" rx="8" fill="#C0C0C0"/>
</svg>'''

# ─── FUN : étoile remplie, bold ───
emojis["fun"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <polygon points="256,60 306,200 460,200 338,290 386,440 256,350 126,440 174,290 52,200 206,200"
           fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="256" cy="256" r="40" fill="#C0C0C0" opacity="0.3"/>
</svg>'''

# ─── STATS : barres hautes, épaisses ───
emojis["stats"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <rect x="70" y="280" width="56" height="160" rx="6" fill="none" stroke="#C0C0C0" stroke-width="14"/>
  <rect x="154" y="180" width="56" height="260" rx="6" fill="none" stroke="#C0C0C0" stroke-width="14"/>
  <rect x="238" y="120" width="56" height="320" rx="6" fill="none" stroke="#C0C0C0" stroke-width="14"/>
  <rect x="322" y="200" width="56" height="240" rx="6" fill="none" stroke="#C0C0C0" stroke-width="14"/>
  <rect x="406" y="90" width="56" height="350" rx="6" fill="none" stroke="#C0C0C0" stroke-width="14"/>
  <line x1="50" y1="450" x2="470" y2="450" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
</svg>'''

# ─── HIÉRARCHIE : couronne large ───
emojis["hierarchie"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <polygon points="80,360 128,180 200,280 256,120 312,280 384,180 432,360"
           fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round" stroke-linecap="round"/>
  <line x1="70" y1="380" x2="442" y2="380" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <circle cx="128" cy="170" r="16" fill="#C0C0C0"/>
  <circle cx="256" cy="110" r="16" fill="#C0C0C0"/>
  <circle cx="384" cy="170" r="16" fill="#C0C0C0"/>
</svg>'''

# ─── TICKETS : billet propre ───
emojis["tickets"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <rect x="60" y="130" width="392" height="252" rx="24" fill="none" stroke="#C0C0C0" stroke-width="18"/>
  <path d="M60 220 C100 220 100 260 60 260" fill="none" stroke="#C0C0C0" stroke-width="16"/>
  <path d="M452 220 C412 220 412 260 452 260" fill="none" stroke="#C0C0C0" stroke-width="16"/>
  <line x1="160" y1="210" x2="360" y2="210" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
  <line x1="160" y1="270" x2="360" y2="270" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
  <line x1="160" y1="330" x2="280" y2="330" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
</svg>'''

# ─── GHOSTPING : fantôme plein, rond ───
emojis["ghostping"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M128 400 L128 280 C128 160 180 100 256 100 C332 100 384 160 384 280 L384 400
           L340 360 L296 400 L256 360 L216 400 L172 360 Z"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="210" cy="250" r="22" fill="#C0C0C0"/>
  <circle cx="302" cy="250" r="22" fill="#C0C0C0"/>
</svg>'''

# ─── WELCOME : main ouverte ───
emojis["welcome"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M180 360 L180 220 C180 200 200 180 220 180 C240 180 260 200 260 220 L260 180
           C260 160 280 140 300 140 C320 140 340 160 340 180 L340 200
           C340 180 360 160 380 160 C400 160 420 180 420 200 L420 360"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M180 360 L420 360" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <path d="M140 380 C140 420 180 440 280 440 C380 440 420 420 420 380"
        fill="none" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
</svg>'''

# ─── AUTOMOD : bouclier avec O ───
emojis["automod"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M256 48 L80 128 L80 260 C80 370 160 450 256 480 C352 450 432 370 432 260 L432 128 Z"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round"/>
  <circle cx="256" cy="260" r="70" fill="none" stroke="#C0C0C0" stroke-width="18"/>
  <circle cx="256" cy="260" r="12" fill="#C0C0C0"/>
</svg>'''

# ─── SALON : dossier ───
emojis["salon"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M80 140 L80 400 C80 416 92 428 108 428 L404 428 C420 428 432 416 432 400 L432 168
           C432 152 420 140 404 140 L240 140 L212 108 L108 108 C92 108 80 120 80 140 Z"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round"/>
  <line x1="80" y1="200" x2="432" y2="200" stroke="#C0C0C0" stroke-width="14"/>
</svg>'''

# ─── BUG : insecte ───
emojis["bug"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <ellipse cx="256" cy="280" rx="90" ry="110" fill="none" stroke="#C0C0C0" stroke-width="18"/>
  <line x1="256" y1="170" x2="256" y2="100" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="256" y1="390" x2="256" y2="440" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="166" y1="240" x2="80" y2="190" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="346" y1="240" x2="432" y2="190" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="166" y1="330" x2="80" y2="380" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="346" y1="330" x2="432" y2="380" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="186" y1="280" x2="130" y2="280" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
  <line x1="326" y1="280" x2="382" y2="280" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
</svg>'''

# ─── SUGGESTION : ampoule ───
emojis["suggestion"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M256 80 C180 80 120 140 120 220 C120 280 160 320 190 340 L190 380 L322 380 L322 340
           C352 320 392 280 392 220 C392 140 332 80 256 80 Z"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round"/>
  <line x1="200" y1="420" x2="312" y2="420" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="210" y1="450" x2="302" y2="450" stroke="#C0C0C0" stroke-width="16" stroke-linecap="round"/>
  <line x1="256" y1="140" x2="256" y2="240" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
  <line x1="256" y1="140" x2="220" y2="180" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
  <line x1="256" y1="140" x2="292" y2="180" stroke="#C0C0C0" stroke-width="14" stroke-linecap="round"/>
</svg>'''

# ─── SUPPORT : roue de secours ───
emojis["support"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <circle cx="256" cy="256" r="160" fill="none" stroke="#C0C0C0" stroke-width="22"/>
  <circle cx="256" cy="256" r="110" fill="none" stroke="#C0C0C0" stroke-width="16"/>
  <circle cx="256" cy="256" r="30" fill="#C0C0C0"/>
  <line x1="256" y1="96" x2="256" y2="146" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <line x1="256" y1="366" x2="256" y2="416" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <line x1="96" y1="256" x2="146" y2="256" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <line x1="366" y1="256" x2="416" y2="256" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
</svg>'''

# ─── REPORT : drapeau planté ───
emojis["report"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <line x1="140" y1="80" x2="140" y2="440" stroke="#C0C0C0" stroke-width="18" stroke-linecap="round"/>
  <path d="M140 80 L400 80 L360 180 L400 280 L140 280"
        fill="none" stroke="#C0C0C0" stroke-width="18" stroke-linejoin="round" stroke-linecap="round"/>
</svg>'''

# ─── AUTRE : point d'interrogation gras ───
emojis["autre"] = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">
  <path d="M200 120 C200 80 312 80 312 120 C312 180 256 200 256 260"
        fill="none" stroke="#C0C0C0" stroke-width="22" stroke-linecap="round"/>
  <circle cx="256" cy="340" r="28" fill="#C0C0C0"/>
</svg>'''


os.makedirs(OUT, exist_ok=True)

for name, svg in emojis.items():
    svg_path = os.path.join(OUT, f"{name}.svg")
    png_path = os.path.join(OUT, f"{name}.png")

    with open(svg_path, "w") as f:
        f.write(svg)

    subprocess.run([
        "rsvg-convert", "-w", str(SIZE), "-h", str(SIZE), svg_path, "-o", png_path
    ], check=True)

    os.remove(svg_path)
    size_kb = os.path.getsize(png_path) / 1024
    print(f"  {name}.png ({size_kb:.1f} KB)")

print(f"\nDone! {len(emojis)} emojis generated.")
