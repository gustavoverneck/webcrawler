from logocrawler import LogoCrawler
import sys
import argparse
import io

# How to use
#$ python py/main.py -f websites.csd -n 8 --verbose


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="run LogoCrawler")
    
    # filename
    parser.add_argument(
        "-f", nargs="?", default=None,
        help="CSV file with list of websites."
    )
    # number of threads
    parser.add_argument(
        "-n", type=int, default=1,
        help="Number of threads to use (default: 1)"
    )
    # verbose
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose output"
    )
    # output file
    parser.add_argument(
        "-o", default="output.csv",
        help="CSV file to store results."
    )
    
    # get args
    args = parser.parse_args()
    
    if args.f:
        input_source = args.f
    else:
        input_source = io.StringIO(sys.stdin.read())    # Read from stdin and create a string buffer
    
    # Initialize Crawler Object
    crawler = LogoCrawler(filename=input_source, 
                          threads_num=args.nt, 
                          verbose=args.verbose,
                          output_file=args.o)