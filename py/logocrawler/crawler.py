# Imports
import os
import requests
import csv
from time import perf_counter

# Internal imports


class LogoCrawler:
    def __init__(self, filename):
        self.readNameDomains()
        print("Crawler initialized.")
    
    def setDomainNames(self, filename):
        if self.filenameExists(filename):
            self.filename = filename
        else:
            raise FileNotFoundError(f"Provided filename `{filename}` does not exist. Please provide a valid filename.")
    
    def printNameDomains(self, nfirst: int):
        print(self.nameDomains[:nfirst])
    
    def run(self):
        print("Running crawler.")
        self.app_start_time = perf_counter()

    def fetchURL(self, url):
        response = requests.get(url)
        if response:
            return
        else:
            return