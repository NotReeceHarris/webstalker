import argparse
import requests

from urllib.parse import urlparse

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import sqlite3
import os

fig, ax = (None, None)

status = {
    'loading': '[ ↻ ]',
    'error': '[ X ]',
    'success': '[ ✓ ]',
}

##!SECTION

def update_chart(frame, fig, ax):
    ax.clear()
    ax.plot(range(frame), [random.random() for i in range(frame)])

def live_update_chart(fig, ax):
    anim = FuncAnimation(fig, update_chart, fargs=(fig, ax), interval=1000)
    plt.show()

###!SECTION

def initialize_chart(target):
    fig, ax = plt.subplots()
    ax.set_title(target)
    return fig, ax

def file_exists(file_path):
    return os.path.exists(file_path)

def create_db(db_file, target):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(f'CREATE TABLE IF NOT EXISTS {urlparse(target).hostname.replace(".", "_")} (id INTEGER PRIMARY KEY, url TEXT, status TEXT)')
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
    print(status['loading'] + ' Checking the availability of the target')
    try:
        response = requests.get(url)
        if response.status_code < 400:
            return True
        else:
            return False
    except:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=str, help='The target url (https://example.com)', required=True)
    parser.add_argument('--depth', type=int, help='Url crawl depth (default: 5)', default=5)
    parser.add_argument('--follow', type=bool, help='Follow just the target (default: True)', default=True)
    parser.add_argument('--rchart', type=bool, help='Generate a relational chart (default: True)', default=True)
    parser.add_argument('--dbpath', type=str, help='Sqlite file path (default: "./data.db")', default='./data.db')
    args = parser.parse_args()

    print(f'Target\t: {args.target}\nDepth\t: {args.depth}\n')

    # Target validation
    if (not validate_url(args.target)):
        exit(status['error'] + ' The target is not a valid url')
    elif (not is_url_up(args.target)):
        exit(status['error'] + ' The target doesnt seem to be available')
    else:
        print(status['success'] + ' Target is valid')

    # Database checks
    if (not file_exists(args.dbpath)):
        print(status['loading'] + f' Generating database: "{args.dbpath}" & Table: "{urlparse(args.target).hostname.replace(".", "_")}"')
        create_db(args.dbpath, args.target)
        print(status['success'] + f' Database and table generated')
    elif (not table_exists(args.dbpath, args.target)):
        print(status['loading'] + f' Generating table: "{urlparse(args.target).hostname.replace(".", "_")}"')
        create_db(args.dbpath, args.target)
        print(status['success'] + f' Table generated')
    
    # Initialize relational chart
    if (args.rchart):
        print(status['loading'] + ' Initializing relational chart')
        fig, ax = initialize_chart(args.target)
        print(status['success'] + f' Initialized relational chart')
        fig.suptitle('WebStalker v1', fontsize=14, fontweight='bold')
        plt.show()

        # Test
        live_update_chart(fig, ax)

if __name__ == '__main__':
    print(' __      __   _    ___ _        _ _           \n \ \    / /__| |__/ __| |_ __ _| | |_____ _ _ \n  \ \/\/ / -_) \'_ \__ \  _/ _` | | / / -_) \'_|\n   \_/\_/\___|_.__/___/\__\__,_|_|_\_\___|_|   v1 \n')
    main()