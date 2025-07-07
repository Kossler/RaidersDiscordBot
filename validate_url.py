from urllib.parse import urlparse

def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except:
        return False
    
def clean_url(url: str) -> str:
    if not url:
        return url
    url = url.replace("\u202f", "")
    url = url.strip()
    return url
