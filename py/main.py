from logocrawler import LogoCrawler

print(__name__)

if __name__ == "__main__":
    filename = "websites.csv"

    # Initialize Crawler Object
    crawler = LogoCrawler(filename)

    # Read domains
    crawler.readNameDomains()

    