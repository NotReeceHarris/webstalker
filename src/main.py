import argparse
from urllib.parse import urlparse
from urllib import robotparser
import sqlite3
import os

from src.utils import status

import requests
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def validate_robots(target, ua):
    rp = robotparser.RobotFileParser()
    rp.set_url(f'{urlparse(target).scheme + "://" + urlparse(target).netloc}/robots.txt')
    rp.read()
    return rp.can_fetch(ua, target)

def init_chart(target):
    fig, ax = plt.subplots()
    ax.set_title(target)
    print(status['success'] + ' Initialized relational chart.')
    fig.suptitle('WebStalker v1', fontsize=14, fontweight='bold')

    for spine in ['left', 'bottom', 'right', 'top']:
        ax.spines[spine].set_visible(False)

    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(axis='both', which='both', length=0)


def file_exists(file_path):
    return os.path.exists(file_path)

def create_db(db_file, target):
    conn = sqlite3.connect(db_file)
    conn.cursor().execute(f'CREATE TABLE IF NOT EXISTS {urlparse(target).hostname.replace(".","_").replace("-","_")} (id INTEGER PRIMARY KEY, url TEXT, via TEXT, status TEXT, scanned INT)')
    conn.commit()
    conn.close()

def table_exists(db_file, target):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (urlparse(target).hostname.replace(".", "_"),))
    result = c.fetchone()
    conn.close()
    return result is not None

def validate_url(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ['http', 'https'] or parsed_url.netloc == "":
        return False
    else:
        return True

def is_url_up(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code < 400:
            return True
        else:
            return False
    except:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--target', type=str, metavar='', help='The target url (\'https://example.com\')', required=True)
    parser.add_argument('-d','--depth', type=int, metavar='', help='Url crawl depth (5)', default=5)
    parser.add_argument('-v','--verbose', help='Print more info about what is being crawled', action='store_true')
    parser.add_argument('--deviate', help='Allow crawling target', action='store_true')
    parser.add_argument('--subdomain', help='Allow crawling of subdomains', action='store_true')
    parser.add_argument('--rchart', help='Generate a relational chart', action='store_true')
    parser.add_argument('--dbpath', type=str, metavar='', help='Sqlite file path (\'./data.db\')', default='./data.db')
    parser.add_argument('--sitemap', type=str, metavar='', help='List of sitemaps (\'https://ex.com/sm.xml, https://ex.com/rss\')')
    parser.add_argument('--ua', type=str, metavar='', help='User agent used by the crawler', default='webstalker/1.0')
    parser.add_argument('--bypass', help='This bypasses crawling restrictions', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        print(f'Target\t: {args.target}\nDepth\t: {args.depth}\nDeviate\t: {"Yes" if args.deviate else "No"}\nUAgent\t: {args.ua}')

    # Validate sitemap
    if (args.sitemap):
        invalid_sitemaps=[]
        if (validate_url(args.target)):
            for sitemap in args.sitemap.replace(' ', '').split(','):
                if (validate_url(sitemap)):
                    if (not sitemap.lower().startswith(f'{urlparse(args.target).scheme + "://" + urlparse(args.target).netloc}'.lower())):
                        invalid_sitemaps.append([sitemap.lower(), 'Sitemap doesn\'t share same origin'])
                else:
                    invalid_sitemaps.append([sitemap.lower(), 'Invalid url'])

        if (len(invalid_sitemaps) != 0):
            print(status['error'] + ' There is an issue with the following sitemap(s):')
            for sitemap in invalid_sitemaps:
                print(f'\'{sitemap[0]}\' : {sitemap[1]}')
            exit('')
        else:
            if args.verbose:
                print(f'Sitemap : {args.sitemap.replace(" ", "").split(",")[0]}')
                for sitemap in args.sitemap.replace(' ', '').split(',')[1:]:
                    print(f'\t  {sitemap}')
                print('')
    else:
        if args.verbose:
            print('')

    # Target validation
    print(status['loading'] + ' Checking the availability of the target.')
    if (not validate_url(args.target)):
        exit(status['error'] + ' The target is not a valid url.\n')
    elif (not is_url_up(args.target)):
        exit(status['error'] + ' The target doesn\'t seem to be available.\n')
    else:
        print(status['success'] + ' Target is valid and accessible.')
    
    # Check robots.txt
    if (not args.bypass):
        print(status['loading'] + ' Checking robots.txt for permission.')
        if (validate_robots(args.target, args.ua)):
            print(status['success'] + ' We can scrape the current target.')
        else:
            print(status['error'] + ' We are not allowed to scrape the target. (use \'--bypass\' to ignore this)')
            exit(status['inform'] + ' The robots.txt parser can be temperamental so this may be a false negative.\n')

    # Database checks
    if (not file_exists(args.dbpath)):
        print(status['loading'] + f' Generating database: "{args.dbpath}" & Table: "{urlparse(args.target).hostname.replace(".","_").replace("-","_")}".')
        create_db(args.dbpath, args.target)
        print(status['success'] + ' Database and table generated.')
    elif (not table_exists(args.dbpath, args.target)):
        print(status['loading'] + f' Generating table: "{urlparse(args.target).hostname.replace(".","_").replace("-","_")}".')
        create_db(args.dbpath, args.target)
        print(status['success'] + ' Table generated.')

    # Initialize relational chart
    if (args.rchart):
        print(status['loading'] + ' Initializing relational chart.')
        init_chart(args.target)

    print(status['inform'] + ' Once crawl has initiated you will not be able to close this process.')
    input(status['input'] + ' Press \'ENTER\' to start crawling...')

    from src.crawler import initiate_scan
    initiate_scan(args.target,args)
