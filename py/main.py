from logocrawler import LogoCrawler

if __name__ == "__main__":
    # Define filename
    filename_ = "websites.csv"
    
    threads_num_ = 8
    
    # Initialize Crawler Object
    crawler = LogoCrawler(filename=filename_, threads_num=threads_num_, verbose=True)