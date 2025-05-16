# LogoCrawler
# Gustavo Arruda Verneck
# May 15 2025

# Imports
import os
import requests
from time import perf_counter, strftime
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Internal imports
from .utils import allowed_file_extensions, log, protocols, request_header

# Disclaim
# This code was documented using LLM.

# -----------------------------------------------------------------------------------

class LogoCrawler:
    """
    LogoCrawler: A web crawler that extracts logo images from websites.
    This class crawls a list of domain names to find their logos using various
    extraction methods. It supports multithreading for parallel processing and
    generates detailed output reports.
    Extraction methods (in order of attempt):
    1. Common logo paths (/logo.png, /images/logo.png, etc.)
    2. OpenGraph image meta tags
    3. Image elements with 'logo' in their ID or class
    4. Favicon links
    Attributes:
        threads_num (int): Number of concurrent threads for crawling
        timeout_time (int): Request timeout in seconds
        verbose (bool): Whether to print detailed progress messages
        output_file (str): Path to save the results CSV file
        metrics_file (str): Path to save the metrics report
        domains_list (list): List of domains to crawl
        results (list): Results of the crawling process
    Methods:
        run(): Executes the crawling process using multiprocessing
        setInputFile(filename): Sets and validates the input file
        checkFileExtension(filename): Validates file extension
        filenameExists(filename): Checks if the input file exists
        readCompleteInputFile(): Reads domains from the input file
        fetchDomain(domain): Fetches and processes a single domain
        parseLogoLink(response): Extracts logo URL from HTTP response
        exportResults(results): Exports crawler results to CSV
        exportMetrics(results): Generates and exports performance metrics
    Example:
        crawler = LogoCrawler(
            filename="domains.txt", 
            threads_num=10, 
            output_file="results.csv",
            metrics_file="metrics.csv",
            verbose=True
        )
    """
    
    def __init__(self, filename=None, threads_num=1, output_file="output.csv", metrics_file="metrics.csv", verbose=False):
        """
        Initializes a new instance of the crawler.
        This constructor sets up the crawler with specified parameters, reads domains from an input file,
        and starts the crawling process.
        Args:
            filename (str, optional): Path to the input file containing domains to crawl. Defaults to None.
            threads_num (int, optional): Number of concurrent threads to use for crawling. Defaults to 1.
            output_file (str, optional): Path to save crawling results. Defaults to "output.csv".
            metrics_file (str, optional): Path to save crawling metrics. Defaults to "metrics.csv".
            verbose (bool, optional): Whether to display detailed output. Defaults to False.
        """
        
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
        """
        Execute the crawler on all domains in the domains list using a process pool.
        This method starts a pool of worker processes based on the specified number of threads,
        processes all domains in parallel, exports the results and metrics, and logs the total
        execution time.
        Returns:
            None
        """
        
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
        """
        Set the input file to be used for processing.
        This method validates the provided filename, ensuring it has the correct extension
        and exists in the filesystem.
        Parameters
        ----------
        filename : str
            Path to the input file.
        Raises
        ------
        FileNotFoundError
            If the provided file does not exist.
        ValueError
            If the file extension is not valid (raised by checkFileExtension method).
        Returns
        -------
        None
            The method sets the instance attribute 'filename' but does not return a value.
        Examples
        --------
        >>> crawler.setInputFile("input_data.csv")
        Successfully defined `input_data.csv` as input file.
        """
        
        self.checkFileExtension(filename)
        if self.filenameExists(filename):
            log(f"Successfully defined `{filename}` as input file.")
            self.filename = filename
        else:
            raise FileNotFoundError(f"Provided filename `{filename}` does not exist. Please provide a valid filename.")
    
    def checkFileExtension(self, filename: str):
        """
        Checks if the file extension is in the list of allowed file extensions.
        This method splits the filename at the dot and verifies the extension 
        against a predefined list of allowed extensions.
        Parameters:
        ----------
        filename : str
            The name of the file to check
        Returns:
        -------
        None
        Raises:
        ------
        ValueError
            If the file extension is not in the list of allowed file extensions
        """
        
        ext = filename.split(".")[1]
        if ext not in allowed_file_extensions:
            raise ValueError(f"Unsupported extension `{ext}`. Expected of of: {', '.join(allowed_file_extensions)}")

    def filenameExists(self, filename):
        """
        Check if a file exists at the given path.
        Args:
            filename (str): The path to the file to check.
        Returns:
            bool: True if the file exists, False otherwise.
        """
        
        return os.path.exists(filename)
    
    def readCompleteInputFile(self):
        """
        Reads the domains from the input file specified by self.filename.
        The method opens the file, reads all lines, and stores the stripped domain names
        in the self.domains_list attribute. Each line in the file is expected to contain
        a single domain name.
        Returns:
            None
        Side effects:
            - Populates self.domains_list with domain names read from the file
            - Logs a success message upon completion
        """
        
        with open(self.filename) as f:
            content = f.readlines()
        self.domains_list = [x.strip() for x in content]
        log("Successfully read domain names from input file.")
    
    def fetchDomain(self, domain: str) -> dict:
        """
        Fetches and processes a website domain to extract logo information.
        This method attempts to access the website using different protocols (http, https)
        and request methods (headed, headless) until a successful response is received.
        It then parses the response to find a logo link.
        Args:
            domain (str): The domain name to fetch (without protocol, e.g., "example.com")
        Returns:
            dict: A dictionary containing the following keys:
                - url (str): The URL with protocol that was successfully accessed, or the original domain if failed
                - logo_link (str): URL to the logo image, or empty string if not found
                - success (bool): True if a logo link was found, False otherwise
                - request_type (str): "headed" when using headers, "headless" without headers, or None if failed
                - message (str): Success message or error description
        Raises:
            No exceptions are raised directly as they are caught and returned in the result dictionary
        """
        
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
                            "message": message if logo_link else f"{last_exception}"    # String: success message or error description
                            }
    
    def parseLogoLink(self, response: requests.Response):
        """
        Extracts logo URL from a website by examining various common locations.
        This method searches for a logo in the following order:
        1. Common logo file paths
        2. Open Graph image meta tag
        3. Image tags with 'logo' in the id or class attributes
        4. Favicon links
        Args:
            response (requests.Response): The HTTP response object from the website
        Returns:
            tuple: A tuple containing:
                - str or None: The URL of the logo if found, None otherwise
                - str: Source of the logo ("common_path", "og_image", "img_logo", "favicon") or "not_found"
        Example:
            >>> logo_url, source = crawler.parseLogoLink(response)
            >>> if logo_url:
            >>>     print(f"Logo found at {logo_url} via {source}")
            >>> else:
            >>>     print("No logo found")
        """
        
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
        """
        Exports the crawling results to a CSV file.
        This method creates an output directory if it doesn't exist,
        then writes the crawling results to a CSV file in that directory.
        The CSV file includes headers and one row per result with fields:
        url, success, logo_link, request_type, and message.
        Args:
            results (list): A list of dictionaries containing the crawling results.
                            Each dictionary should have keys: 'url', 'success',
                            'logo_link', 'request_type', and 'message'.
        Returns:
            None
        Side effects:
            - Creates 'output' directory if it doesn't exist
            - Writes to a file at self.output_file
            - Updates self.output_file to include the 'output/' directory prefix
        """
        
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
        """
        Export metrics about logo extraction attempts to a file.
        This method processes a list of logo extraction results and generates comprehensive metrics,
        including success/failure rates, types of successes/failures, and request type distribution.
        The metrics are written to a file specified by self.metrics_file in the output directory.
        Parameters:
        -----------
        results : list
            A list of dictionaries, where each dictionary represents the result of a logo extraction attempt.
            Expected keys in each dictionary:
            - 'success': bool, whether the extraction was successful
            - 'message': str, success type or error message
            - 'request_type': str, type of request ('headed', 'headless', or None if failed)
        Returns:
        --------
        None
            Metrics are written to a file, no value is returned.
        Side Effects:
        -------------
        - Creates an 'output' directory if it doesn't exist
        - Writes metrics to self.metrics_file in the output directory
        """
        
        log(f"Exporting metrics to output/{self.metrics_file}")

        # Create output directory if it doesn't exist
        os.makedirs("output", exist_ok=True)
        self.metrics_file = f"output/{self.metrics_file}"

        # Calculate metrics
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = total_requests - successful_requests

        # Success message types breakdown
        success_types = {}
        for result in results:
            if result['success']:
                msg_type = result['message']
                success_types[msg_type] = success_types.get(msg_type, 0) + 1

        # Error message types breakdown
        error_types = {}
        for result in results:
            if not result['success']:
                error_msg = result['message']
                error_types[error_msg] = error_types.get(error_msg, 0) + 1

        # Request types
        headed_requests = sum(1 for r in results if r['request_type'] == 'headed')
        headless_requests = sum(1 for r in results if r['request_type'] == 'headless')
        failed_req_count = sum(1 for r in results if r['request_type'] is None)

        # Write metrics to file
        with open(self.metrics_file, "w+") as f:
            f.write(f"Total domains processed: {total_requests}\n")
            f.write(f"Successful logo extractions: {successful_requests} ({successful_requests/total_requests*100:.2f}%)\n")
            f.write(f"Failed extractions: {failed_requests} ({failed_requests/total_requests*100:.2f}%)\n\n")
            
            f.write("Success Breakdown:\n")
            for success_type, count in sorted(success_types.items(), key=lambda x: x[1], reverse=True):
                percent_of_success = (count / successful_requests * 100) if successful_requests > 0 else 0
                percent_of_total = (count / total_requests * 100)
                f.write(f"- {success_type}: {count} ({percent_of_success:.2f}% of successful, {percent_of_total:.2f}% of total)\n")
            
            f.write("\nFailure Breakdown:\n")
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                percent_of_failures = (count / failed_requests * 100) if failed_requests > 0 else 0
                percent_of_total = (count / total_requests * 100)
                f.write(f"- {error}: {count} ({percent_of_failures:.2f}% of failures, {percent_of_total:.2f}% of total)\n")
            
            f.write("\nRequest Types:\n")
            f.write(f"- Headed requests: {headed_requests} ({headed_requests/total_requests*100:.2f}%)\n")
            f.write(f"- Headless requests: {headless_requests} ({headless_requests/total_requests*100:.2f}%)\n")
            f.write(f"- Failed requests: {failed_req_count} ({failed_req_count/total_requests*100:.2f}%)\n\n")
            
            f.write("Common error messages:\n")
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {error}: {count} ({count/total_requests*100:.2f}%)\n")
