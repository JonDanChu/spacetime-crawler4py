import re
import requests

from lxml import html
from urllib.parse import urlparse, urljoin

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
    
    # write code to check the response code first from resp

    links = []
    
    if resp.status != 200:
        print(f"For:{url}\nResponse Code:{resp.status}\n")
        return
    
    # Get the content from the response
    tree = html.fromstring(resp.content)

    # Extract elements using XPath
    text = tree.xpath('//body/text()')  # Get all <h1> text

    if length(text) < 100:
        return links
    links = tree.xpath('//a/@href')     # Get all link URLs

    # Defragmentation should be done here
    
    nw_links = list()
    for edit_link in links:
        loc = edit_link.find('#')
        if loc > -1:
            # Test if the fragment is for the same webpage
            if loc == 0:
                continue

            edit_link = edit_link[0:loc]

        # things like mailto: will still be identifiable
        edit_link = urljoin(url, edit_link)

        nw_links.append(edit_link)
    
    return nw_links

    # if we want to just ignore them instead
    # for check_link in links:
    #     #check claude for how to filter out urls from href
    #     if check_link.find('#'):
    #         links.remove(check_link)

    # return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not re.match(
            r".*\.(ics\.uci\.edu/|cs\.uci\.edu/|informatics\.uci\.edu/|stat\.uci\.edu/)$",
            parsed.hostname.lower()):
            return False
        
        if not re.match(
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
