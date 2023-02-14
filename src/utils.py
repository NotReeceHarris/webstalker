""" https://gist.github.com/rene-d """
BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
BROWN = "\033[0;33m"
BLUE = "\033[0;34m"
PURPLE = "\033[0;35m"
CYAN = "\033[0;36m"
LIGHT_GRAY = "\033[0;37m"
DARK_GRAY = "\033[1;30m"
LIGHT_RED = "\033[1;31m"
LIGHT_GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
LIGHT_BLUE = "\033[1;34m"
LIGHT_PURPLE = "\033[1;35m"
LIGHT_CYAN = "\033[1;36m"
LIGHT_WHITE = "\033[1;37m"
BOLD = "\033[1m"
FAINT = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
NEGATIVE = "\033[7m"
CROSSED = "\033[9m"
END = "\033[0m"


if not __import__("sys").stdout.isatty():
    for _ in dir():
        if isinstance(_, str) and _[0] != "_":
            locals()[_] = ""
else:
    if __import__("platform").system() == "Windows":
        kernel32 = __import__("ctypes").windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        del kernel32

hero = f"""         
  {LIGHT_GRAY}/ _ \{END}    __      __   _    ___ _        _ _             
{LIGHT_GRAY}\_\({LIGHT_RED}X{END}{LIGHT_GRAY})/_/{END}  \ \    / /__| |__/ __| |_ __ _| | |_____ _ _   
 {LIGHT_GRAY}_//"\\\_{END}    \ \/\/ / -_) '_ \__ \  _/ _` | | / / -_) '_| 
  {LIGHT_GRAY}/   \{END}      \_/\_/\___|_.__/___/\__\__,_|_|_\_\___|_|   
"""

status = {
    'loading': f'[ {CYAN}↻{END} ]',
    'error': f'[ {BOLD}{RED}X{END} ]',
    'success': f'[ {GREEN}✓{END} ]',
    'inform': f'[ {BOLD}{YELLOW}!{END} ]',
    'question': f'[ {BOLD}{BLUE}?{END} ]',
    'input': f'[ {BOLD}{PURPLE}>{END} ]',
}
