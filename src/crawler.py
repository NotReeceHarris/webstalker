from sqlite3 import connect as sqlite_connect
from urllib.parse import urlparse, urlunparse
from urllib import robotparser
from urllib3 import exceptions
from time import sleep

import requests
from bs4 import BeautifulSoup
from src.utils import status

scanned_urls = 0;
found_urls = 0;

def validate_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https'] or parsed_url.netloc == "":
        return False
    else:
        return True

def same_parent_domain(url1, url2):
    # check if the last two parts of the hostname are the same
    return urlparse(url1).netloc.split(".")[-2:] == urlparse(url2).netloc.split(".")[-2:]

def already_scanned(link,args):
    if (link.endswith('/')):
        link = link[:-1]

    conn = sqlite_connect(args.dbpath)
    cursor = conn.cursor()

    cursor.execute(f'SELECT `url` FROM {urlparse(args.target).hostname.replace(".","_").replace("-","_")} WHERE `url` = ? AND `scanned` = 1', (link,))

    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    return len(rows) >= 1

def scanned(url, parent, status, args):
    if (url.endswith('/')):
        url = url[:-1]
    
    if (parent.endswith('/')):
        parent = parent[:-1]

    conn = sqlite_connect(args.dbpath)
    cursor = conn.cursor()

    cursor.execute(f'UPDATE {urlparse(args.target).hostname.replace(".","_").replace("-","_")} SET `status` = ?, `scanned` = 1 WHERE `url` = ? ', (status, url))
    
    conn.commit()
    conn.close()

def add_to_db(url,parent,scanned,args):

    if (url.endswith('/')):
        url = url[:-1]
    
    if (parent.endswith('/')):
        parent = parent[:-1]

    conn = sqlite_connect(args.dbpath)
    cursor = conn.cursor()

    cursor.execute(f'SELECT `url` FROM {urlparse(args.target).hostname.replace(".","_").replace("-","_")} WHERE `url` = ? AND `via` = ? LIMIT 1', (url, parent))
    rows = cursor.fetchall()

    if (len(rows) != 1):
        cursor.execute(f'SELECT * FROM {urlparse(args.target).hostname.replace(".","_").replace("-","_")} WHERE `url` = ? AND `scanned` = 1', (url,))
        if len(cursor.fetchall()) >= 1:
            scanned = 1
        cursor.execute(f'INSERT INTO {urlparse(args.target).hostname.replace(".","_").replace("-","_")} (`url`, `via`, `scanned`) VALUES (?,?,?)', (url, parent, scanned))

    conn.commit()
    conn.close()

def next_scan(args):
    conn = sqlite_connect(args.dbpath)
    cursor = conn.cursor()

    cursor.execute(f'SELECT `url`, `via` FROM {urlparse(args.target).hostname.replace(".","_").replace("-","_")} WHERE `scanned` = 0  ORDER BY `id` DESC LIMIT 1')

    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    return rows

def crawl(url,args,parent):
    global scanned_urls
    global found_urls

    if not args.verbose:
        print(f'{status["loading"]} Scanned: {scanned_urls}, Found: {found_urls}', end='\r', flush=True)

    can_crawl = True
    found = 0
    current_status = 0

    if (not already_scanned(url, args) or parent == "Initial scan"):
        if (args.verbose):
            print(f'{status["loading"]} Scanning "{url}" found from "{parent}"')

        if (not args.bypass):
            robot_parser = robotparser.RobotFileParser()
            robot_parser.set_url(f'{urlparse(url).scheme + "://" + urlparse(url).netloc}/robots.txt')
            robot_parser.read()
            can_crawl = robot_parser.can_fetch(args.ua, url)
        
        if (can_crawl):
            try:
                response = requests.get(url, timeout=args.timeout)
                current_status = response.status_code
                scanned_urls += 1
                add_to_db(url, parent, 1, args)

                # check if the request was successful
                if response.status_code == 200:
                    # parse the HTML content of the website
                    soup = BeautifulSoup(response.content, "html.parser")

                    # find all "a" tags
                    links = soup.find_all("a")
                    # print the href attribute of each link
                    for link in links:
                        href = link.get("href")
                        if href:
                            if not args.query:
                                href = href.split("?")[0]
                            
                            full_url = urlunparse((urlparse(url).scheme, urlparse(url).netloc, '', '', '', ''))

                            if validate_url(href):
                                if href.lower().startswith(full_url):
                                    if not already_scanned(href,args):
                                        found+=1
                                        add_to_db(href,url,0,args)
                                    else:
                                        found+=1
                                        add_to_db(href,url,1,args)

                                elif args.deviate or (same_parent_domain(href, args.target) and args.subdomain):
                                    if not already_scanned(href,args):
                                        found+=1
                                        add_to_db(href,url,0,args)
                                    else:
                                        found+=1
                                        add_to_db(href,url,1,args)

                            elif urlparse(href).scheme not in ['http', 'https'] or urlparse(href).netloc == "":
                                link_url = full_url + href
                                if validate_url(link_url) and not any(href.lower().startswith(prefix) for prefix in ['mailto:', 'tel:', '#', 'ftp:', 'file:', 'news:', 'gopher:', 'nntp:', 'telnet:', 'ssh:', 'javascript:', '{']):
                                    if not already_scanned(link_url,args):
                                        found+=1
                                        add_to_db(link_url,url,0,args)
                                    else:
                                        found+=1
                                        add_to_db(link_url,url,1,args)
                if (args.verbose):
                    if found == 0:
                        print(f'{status["inform"]} Nothing found to crawl on this site.')
                    else:
                        print(f'{status["success"]} Found {found} crawlable links on this site.')
                found_urls += found
            except KeyboardInterrupt:
                if (args.verbose):print('+---=========================---+\n')
                exit(f'{status["inform"]} Stopping crawling.')
            except:
                pass
        elif args.verbose:
            print(f'{status["error"]} Robots.txt won\'t let us scrape "{url}"')


            
    scanned(url, parent, current_status, args)
    sleep(args.delay)
    next = next_scan(args)
    if len(next) == 1:
        crawl(next[0][0], args, next[0][1])
    else:
        if (args.verbose):print('+---=========================---+\n')
        print(f'{status["success"]} Everything has been crawled. To access the data view "{args.dbpath}"')

def initiate_scan(url,args):
    if (args.verbose):print('\n+---====[ CRAWL FEEDACK ]====---+')
    else:print(f'{status["inform"]} Please wait while we crawl, this could take a couple hours depending on your input.')
    crawl(url,args,"Initial scan")