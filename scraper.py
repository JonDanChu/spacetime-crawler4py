import re
from threading import Lock

from lxml import html
from urllib.parse import parse_qsl, urlparse, urljoin, urldefrag

TRAP_LOCK = Lock()
SEEN_TRAP_PATTERNS = {}
SEEN_TRAP_URLS = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link) and not is_trap(link)]

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
    # check for content type, only parse html pages
    if "html" not in resp.raw_response.headers.get("Content-Type", "").lower():
        return links

    # Get the content from the response
    try:
        tree = html.fromstring(resp.raw_response.content)
    except Exception as e:
        print(f"Failed to parse {url}: {e}")
        return links

    # Check for information content 
    raw_text = tree.text_content() 
    words = [] 
    for w in raw_text.lower().split():
        if w.isalpha(): 
            words.append(w)
    if len(words) < 100:
        return links

    raw_links = tree.xpath('//a/@href')     # Get all link URLs

    for link in raw_links:
        absolute = urljoin(url, link)
        defragmented, _ = urldefrag(absolute)
        links.append(defragmented)

    return links

def is_trap(url):
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    query_parts = parse_qsl(parsed.query, keep_blank_values = False)
    query_keys = [key.lower() for key, _ in query_parts]
    url_length = len(url)
    path_depth = len(path_parts)
    query_count = len(query_parts)
    unique_query_count = len(set(query_keys))
    numeric_part_count = 0
    repeated_part_count = 0

    # Check for common crawler traps.
    if url_length > 2000:
        return True
    if path_depth > 12:
        return True
    if query_count > 8:
        return True
    if query_count != unique_query_count:
        return True
    
    # Count repeated numeric parts in the path.
    for part in path_parts:
        if part.isdigit():
            numeric_part_count += 1
    if numeric_part_count > 4: # If there are more than 4 numeric parts, it's likely a trap
        return True
    
    # Count the maximum number of times any single part is repeated in the path.
    for part in set(path_parts):
        repeated_part_count = max(repeated_part_count, path_parts.count(part))
    if repeated_part_count > 3: # If any single part is repeated more than 3 times, it's likely a trap
        return True

    # Create a trap key that strips away variable parts of the URL
    # ( hostname, path pattern)
    trap_key = (
        parsed.hostname.lower(),
        tuple(re.sub(r"\d+", "{num}", part.lower()) for part in path_parts),
    )

    # If we keep seeing new URLs with the same shape, it is usually a calendar,
    # faceted search, or session-style infinite trap.
    with TRAP_LOCK:
        if url in SEEN_TRAP_URLS:
            count = SEEN_TRAP_PATTERNS.get(trap_key, 0)
        else:
            # Only count genuinely new URLs toward the trap-pattern limit.
            SEEN_TRAP_URLS.add(url)
            count = SEEN_TRAP_PATTERNS.get(trap_key, 0) + 1
            SEEN_TRAP_PATTERNS[trap_key] = count

    return count > 100

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]) or not parsed.hostname:
            return False
        
        if not re.match(
            r"(grape\.ics\.uci\.edu)$",
            parsed.hostname.lower()):
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
