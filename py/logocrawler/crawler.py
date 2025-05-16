# Imports
import os
import requests
from time import perf_counter, strftime
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Internal imports
from .utils import allowed_file_extensions, log, protocols, request_header

# -----------------------------------------------------------------------------------

class LogoCrawler:
    def __init__(self, filename=None, threads_num=1, output_file="output.csv", metrics_file="metrics.csv", verbose=False):
        # Crawler properties
        self.threads_num = threads_num  # Number of concurrent processes
        self.timeout_time = 5  # Define timeout time
        self.verbose = verbose
        self.output_file = output_file
        self.metrics_file = metrics_file

        # Crawler variables
        self.domains_list = []  # List of all urls to be fetched
        self.results = []   # Results from fetched urls
        log("Crawler initialized.")
        
        # Execute
        self.setInputFile(filename)
        self.readCompleteInputFile()
        self.run()
    
    def run(self):
        log(f"Running Crawler using {self.threads_num} thread(s) for {len(self.domains_list)} name domains.")
        self.app_start_time = perf_counter()
        with Pool(processes=self.threads_num) as pool:
            results = pool.map(self.fetchDomain, self.domains_list)
        self.exportResults(results)
        self.exportMetrics(results)
        
        # Finish
        app_end_time = perf_counter()
        total_time = app_end_time - self.app_start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = total_time % 60
        print(f"Crawler finished in {hours}h {minutes}m {seconds:.2f}s")
        
    def setInputFile(self, filename):
        self.checkFileExtension(filename)
        if self.filenameExists(filename):
            log(f"Successfully defined `{filename}` as input file.")
            self.filename = filename
        else:
            raise FileNotFoundError(f"Provided filename `{filename}` does not exist. Please provide a valid filename.")
    
    def checkFileExtension(self, filename: str):
        ext = filename.split(".")[1]
        if ext not in allowed_file_extensions:
            raise ValueError(f"Unsupported extension `{ext}`. Expected of of: {', '.join(allowed_file_extensions)}")

    def filenameExists(self, filename):
        return os.path.exists(filename)
    
    def readCompleteInputFile(self):
        with open(self.filename) as f:
            content = f.readlines()
        self.domains_list = [x.strip() for x in content]
        log("Successfully read domain names from input file.")
    
    def fetchDomain(self, domain: str):
        if self.verbose: log(f"Fetching: {domain}")
        
        last_exception = None
        response = None
        logo_link = None
        header_type = None
        url = None
        message = "not_attempted"
        
        # Try 'http' and 'https' and 'no' protocols
        for protocol in protocols:
            url = protocol + domain
            # Try headed and headless requests
            try:
                # Headed request
                response = requests.get(url, timeout=self.timeout_time, headers=request_header)
                if response:
                    header_type = "headed"
                    break                    
                else:
                    # Headless request if failed headed request
                    response = response = requests.get(url, timeout=self.timeout_time)
                    if response:
                        header_type = "headless"
                        break
                
            except Exception as e:
                last_exception = f"Error {e.__class__.__name__}"
                if hasattr(e, 'response') and e.response is not None:
                    last_exception = f"{e.response.status_code}"
        
        if response:
            logo_link, message = self.parseLogoLink(response)
        
        return {"url": url if response else domain,                                     # The URL with protocol (e.g., "https://example.com")
                            "logo_link": f"{logo_link}",                                # URL to the logo image or None if not found
                            "success": True if logo_link else False,                    # Boolean: True if found logo_link, False otherwise
                            "request_type": header_type if response else None,          # String: "headed" when using headers, "headless" without headers
                            "message": message if logo_link else f"{last_exception}"  # String: success message or error description
                            }
    
    def parseLogoLink(self, response: requests.Response):
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = response.url

        # Search order: common_paths -> og:image -> img_logo -> favicon
        
        # Common Paths
        common_logo_paths = [
            "/logo.png", 
            "/images/logo.png", 
            "/static/logo.svg", 
            "/assets/logo.png", 
            "/img/logo.png"
            ]
        
        # Try to find logo in common paths
        for path in common_logo_paths:
            logo_url = urljoin(base_url, path)
            try:
                res = requests.head(logo_url, timeout=5)
                if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
                    return logo_url, "common_path"
            except:
                continue
            
        # Try to find logo in meta og:image tag or content
        meta_og_tags = soup.find('meta', property='og:image')
        if meta_og_tags:
            content = meta_og_tags.get('content')
            if content:
                logo_url = urljoin(base_url, content)
                return logo_url, "og_image"

        # Try to find logo in <img> with id='logo' or class='logo'
        img_tags = soup.find_all('img')
        for img_tag in img_tags:
            classes = img_tag.get('class', [])
            if img_tag.get('id') == 'logo' or any('logo' in c.lower() for c in classes):
                src = img_tag.get('src')
                if src:
                    logo_url = urljoin(base_url, src)
                    return logo_url, "img_logo"

        # Try to find icon in <link rel="icon"> or <link rel="shortcut icon">
        link_icons = soup.find_all('link', rel=lambda x: x and 'icon' in x.lower())
        for link_tag in link_icons:
            href = link_tag.get('href')
            if href:
                logo_url = urljoin(base_url, href)
                return logo_url, "favicon"

        # Failed: logo not found
        return None, "not_found"
        
    def exportResults(self, results: list):
        log(f"Exporting results to output/{self.output_file}")
        
        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        
        self.output_file = f"output/{self.output_file}"
        
        # Output each result to output file
        with open(self.output_file, "w+") as f:
            # Write header row
            f.write("url, success, logo_link, request_type, message\n")
            # Results            
            for result in results:
                f.write(f"{result['url']}, {result['success']}, \"{result['logo_link']}\", {result['request_type']}, \"{result['message']}\"\n")

    def exportMetrics(self, results: list):
        log(f"Exporting metrics to {self.metrics_file}")

        # Create output directory if it doesn't exist
        metrics_path = os.path.join('output', self.metrics_file)
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        self.metrics_file = metrics_path

        # Calculate metrics
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r['success'])
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0

        # Count request types
        headed_requests = sum(1 for r in results if r['request_type'] == 'headed')
        headless_requests = sum(1 for r in results if r['request_type'] == 'headless')
        failed_requests = sum(1 for r in results if r['request_type'] is None)

        # Categorize failures
        connection_failures = sum(1 for r in results if not r['success'] and r['request_type'] is None)
        not_found_failures = sum(1 for r in results if not r['success'] and r['message'] == "not_found")
        other_failures = (total_requests - successful_requests) - (connection_failures + not_found_failures)

        # Common error messages
        error_types = {}
        for result in results:
            if not result['success']:
                error_msg = result['message']
                error_types[error_msg] = error_types.get(error_msg, 0) + 1
        
        # Write metrics to file
        with open(self.metrics_file, "w+") as f:
            f.write(f"Total domains processed: {total_requests}\n")
            f.write(f"Successful logo extractions: {successful_requests} ({success_rate:.2f}%)\n")
            f.write(f"Failed extractions: {total_requests - successful_requests} ({100 - success_rate:.2f}%)\n\n")
            
            f.write("Failure Breakdown:\n")
            f.write(f"- Connection failures: {connection_failures} ({connection_failures/total_requests*100:.2f}%)\n")
            f.write(f"- Logo not found: {not_found_failures} ({not_found_failures/total_requests*100:.2f}%)\n")
            f.write(f"- Other failures: {other_failures} ({other_failures/total_requests*100:.2f}%)\n\n")
            
            f.write("Request Types:\n")
            f.write(f"- Headed requests: {headed_requests} ({headed_requests/total_requests*100:.2f}%)\n")
            f.write(f"- Headless requests: {headless_requests} ({headless_requests/total_requests*100:.2f}%)\n")
            f.write(f"- Failed requests: {failed_requests} ({failed_requests/total_requests*100:.2f}%)\n\n")
            
            f.write("Common error messages:\n")
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {error}: {count} ({count/total_requests*100:.2f}%)\n")