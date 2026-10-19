"""Download Shark Tank India Season 1 shark portraits for offline use.

Run: python download_shark_photos.py
This script downloads publicly reachable image URLs into assets/sharks/*.jpg.
Check each source site's terms and permissions before redistributing the images.
"""
from io import BytesIO
from pathlib import Path
import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "sharks"
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = {'aman': 'https://m.economictimes.com/thumb/height-450%2Cwidth-600%2Cimgsize-26466%2Cmsid-125719833/aman-gupta.jpg', 'anupam': 'https://images.moneycontrol.com/static-mcnews/2022/06/Shaadi.com-founder-Anupam-Mittal-is-also-a-judge-on-Shark-Tank-India.jpg?height=900&impolicy=website&width=1600', 'ashneer': 'https://m.media-amazon.com/images/M/MV5BN2YyMjNhZDctNTRlOC00MTExLThmYTUtN2QyNjU5NDBkMDFmXkEyXkFqcGc%40._V1_.jpg', 'ghazal': 'https://www.hindustantimes.com/ht-img/img/2024/04/24/1600x900/20211223_214947_0000_1645255026651_1713961535591.jpg', 'namita': 'https://mxp-media.ilnmedia.com/media/content/2024/Feb/Image-1_65ceeedc541d8.jpeg?cc=1&h=896&w=780', 'peyush': 'https://staticimg.publishstory.co/thumb/127423844.cms?height=900&imgsize=53376&resizemode=8&width=1200', 'vineeta': 'https://d28wu8o6itv89t.cloudfront.net/images/VineetaSinghjpg-1709202897464.jpeg'}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SharkTankAI educational project)"}
for name, url in SOURCES.items():
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        image = ImageOps.fit(image, (600, 600), method=Image.Resampling.LANCZOS, centering=(0.5, 0.35))
        image.save(OUT / f"{name}.jpg", quality=90, optimize=True)
        print(f"Downloaded {name}.jpg")
    except Exception as exc:
        print(f"Could not download {name}: {exc}. Local initials placeholder will be used.")
