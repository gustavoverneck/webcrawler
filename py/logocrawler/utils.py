from time import strftime

allowed_file_extensions = ["txt", "csv", "dat"]

desired_img_extensions = ["png"]

protocols = ["http://", "https://"]

def log(message):
    timestamp = strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
        