# Internal imports
from .crawler import LogoCrawler

# -----------------------------------------------------------

class Test:
    def __init__(self):
        pass
    
    def checkCrawler(self, filename):
        crawler = LogoCrawler(filename)
        