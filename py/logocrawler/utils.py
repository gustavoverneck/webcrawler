from time import strftime

allowed_file_extensions = ["txt", "csv", "dat"]

protocols = ["https://www.", "http://www.", "www."]

request_header = HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
    }

def log(message: str):
    timestamp = strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
        
