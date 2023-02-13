import requests
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib import robotparser

def validate_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https'] or parsed_url.netloc == "":
        return False
    else:
        return True

def same_parent_domain(url1, url2):
    # parse the URLs into components
    url1_parsed = urlparse(url1)
    url2_parsed = urlparse(url2)
    
    # extract the netloc (hostname) from each URL
    url1_host = url1_parsed.netloc
    url2_host = url2_parsed.netloc
    
    # split the hostname into parts
    url1_parts = url1_host.split(".")
    url2_parts = url2_host.split(".")
    
    # check if the last two parts of the hostname are the same
    if url1_parts[-2:] == url2_parts[-2:]:
        return True
    else:
        return False

def already_scanned(link,args):
    # Connect to the database
    conn = sqlite3.connect(args.dbpath)

    # Create a cursor object
    cursor = conn.cursor()

    # Select all rows from the 'urls' table
    cursor.execute(f'SELECT * FROM {urlparse(args.target).hostname.replace(".","_").replace("-","_")} WHERE `url` = "{link}"')

    # Fetch all rows
    rows = cursor.fetchall()

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()

    return len(rows) >= 1

def add_to_db(url,parent,scanned,status,args):

    if (url.endswith('/')):
        url = url[:-1]

    print(f'{parent} > {url} | {scanned}')
    # Connect to the database
    conn = sqlite3.connect(args.dbpath)

    # Create a cursor object
    cursor = conn.cursor()

    cursor.execute(f'SELECT * FROM {urlparse(args.target).hostname.replace(".","_").replace("-","_")} WHERE `url` = ? AND via = ?', (url, parent))
    rows = cursor.fetchall()

    if (len(rows) <= 0):
        cursor.execute(f'INSERT INTO {urlparse(args.target).hostname.replace(".","_").replace("-","_")} (`url`, `via`, `status`, `scanned`) VALUES (?,?,?,?)', (url, parent, status, scanned))

    conn.commit()
    conn.close()

def next_scan():
    pass

def crawl(url,args,parent):

    can_crawl = True

    if (not args.bypass):
        rp = robotparser.RobotFileParser()
        rp.set_url(f'{urlparse(url).scheme + "://" + urlparse(url).netloc}/robots.txt')
        rp.read()
        can_crawl = rp.can_fetch(args.ua, url)
    
    if (can_crawl):

        response = requests.get(url)

        # check if the request was successful
        if response.status_code == 200:
            # parse the HTML content of the website
            soup = BeautifulSoup(response.content, "html.parser")

            # find all "a" tags
            links = soup.find_all("a")

            add_to_db(url,parent,1,response.status_code,args)

            # print the href attribute of each link
            for link in links:
                href = link.get("href")
                if href:
                    if not already_scanned(href,args):
                        if validate_url(href):
                            full_url = urlparse(url).scheme + "://" + urlparse(url).netloc
                            if href.lower().startswith(full_url):
                                add_to_db(href,url,0,response.status_code,args)

                            elif args.deviate or (same_parent_domain(href, args.target) and args.subdomain):
                                add_to_db(href,url,0,response.status_code,args)
                        elif urlparse(href).scheme not in ['http', 'https'] or urlparse(href).netloc == "":
                            full_url = urlparse(url).scheme + "://" + urlparse(url).netloc
                            link_url = full_url + href
                            if not already_scanned(link_url,args):
                                if validate_url(link_url) and not any(href.lower().startswith(prefix) for prefix in ['mailto:', 'tel:', '#', 'ftp:', 'file:', 'news:', 'gopher:', 'nntp:', 'telnet:', 'ssh:']):
                                    add_to_db(link_url,url,0,response.status_code,args)
                            else:
                                add_to_db(link_url,url,1,0,args)
                    else:
                        add_to_db(href,url,1,0,args)

        else:
            add_to_db(url,parent,1,response.status_code,args)

        next_scan()

def initiate_scan(url,args):
    crawl(url,args,"Initial scan")