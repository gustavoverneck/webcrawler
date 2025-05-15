# Imports
import os
import requests
import csv
from time import perf_counter, strftime
from multiprocessing import Pool

# Internal imports
from .utils import allowed_file_extensions, desired_img_extensions, log, protocols

# -----------------------------------------------------------------------------------

class LogoCrawler:
    def __init__(self, filename=None, threads_num=1, output_file="output.csv", metrics_file="metrics.csv", verbose=False):
        # Crawler properties
        self.threads_num = threads_num  # Number of concurrent processes
        self.timeout_time = 10  # Define timeout time
        self.verbose = verbose
        self.output_file = output_file
        self.metrics_file = metrics_file

        # Crawler variables
        self.url_list = []  # List of all urls to be fetched
        self.results = []   # Results from fetched urls
        log("Crawler initialized.")
        
        # Execute
        self.setInputFile(filename)
        self.readCompleteInputFile()
        self.run()
    
    def run(self):
        log(f"Running Crawler with {self.threads_num} threads for {len(self.url_list)} URLs.")
        self.app_start_time = perf_counter()
        with Pool(processes=self.threads_num) as pool:
            results = pool.map(self.fetchURL, self.url_list)
        self.exportResults(results)
        self.exportMetrics(results)
        
    def setInputFile(self, filename):
        self.checkFileExtension(filename)
        if self.filenameExists(filename):
            log(f"Sucessfully defined `{filename}` as input file.")
            self.filename = filename
        else:
            raise FileNotFoundError(f"Provided filename `{filename}` does not exist. Please provide a valid filename.")
    
    def checkFileExtension(self, filename: str):
        ext = filename.split(".")[1]
        if ext not in allowed_file_extensions:
            raise ValueError(f"Unsupported extension `{ext}`. Expected of of: {', '.join(allowed_file_extensions)}")

    def filenameExists(self, filename):
        if os.path.exists(filename):
            return True
        else:
            return False
    
    def readCompleteInputFile(self):
        with open(self.filename) as f:
            content = f.readlines()
        self.url_list = [x.strip() for x in content]
        log("Sucessfully read domain names from input file.")
    
    def fetchURL(self, url):
        if self.verbose: log(f"Fetching: {url}")
        try:
            response = requests.get(url, timeout=self.timeout_time)
            if response:
                logo_url = self.getLogoURL(response)
                
                return {"url": url,
                        "logo_url": logo_url,
                        "success": True,
                        "message": "success"
                        }
        except Exception as e:
            return {"url": url,
                    "logo_url": None,
                    "success": False,
                    "message": str(e)
                    }
    
    def getLogoURL(self, response):
        return "https://example.com/logo.png"

    def exportResults(self, results: list):
        with open(self.output_file, "w+") as f:
            fieldnames = ['url', 'logo_url', 'success', 'message']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result)

    def exportMetrics(self, results: list):
        pass