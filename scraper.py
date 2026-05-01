import re
import time
import configparser

from lxml import html
from urllib.parse import urlparse, urljoin, urldefrag

from collections import defaultdict

prev_domain = ""
link_set = set() # Use this for the time being to identify unique urls that we have checked out

trap = defaultdict(int) # key - tuple (domain,path) key - number of accesses
TRAP_THRESHOLD = 5

config = configparser.ConfigParser()
config.read('config.ini')
DELAY = float(config['CRAWLER']['POLITENESS'])

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    # politness break
    # need to make more specific for each domain later
    time.sleep(DELAY)

    # write code to check the response code first from resp
    if resp.raw_response is None: 
        return[] 

    links = []
    
    if resp.status != 200:
        print(f"For:{url}\nResponse Code:{resp.status}\nError:{resp.error}")

        return links

    # check for empty or very large content 
    if len(resp.raw_response.content) == 0: 
        return links
    if len(resp.raw_response.content) > 10_000_000:
        return links 

    # Get the content from the response
    try:
        tree = html.fromstring(resp.raw_response.content)
    except Exception as e:
        print(f"Failed to parse {url}: {e}")
        return links

    # to check for traps
    parsed = urlparse(url)
    key = (parsed.netloc, parsed.path)

    #check for information content 
    raw_text = tree.text_content() 
    words = [] 
    for w in raw_text.lower().split():
        if w.isalpha(): 
            words.append(w)
    if len(words) < 100:
        return links
    else:
        trap[key] = 0

    raw_links = tree.xpath('//a/@href')     # Get all link URLs

    # Defragmentation should be done here
    for link in raw_links:
        absolute = urljoin(url, link)
        defragmented = urldefrag(absolute)[0]

        parsed = urlparse(defragmented)

        key = (parsed.netloc, parsed.path)

        trap[key] += 1

        if trap[key] > TRAP_THRESHOLD:
            continue
        
        if defragmented not in link_set:
            links.append(defragmented)
            link_set.add(defragmented)

    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not re.match(
            r"(.*\.)?(ics\.uci\.edu|cs\.uci\.edu|informatics\.uci\.edu|stat\.uci\.edu)$",
            parsed.hostname.lower()):
            return False
        
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
