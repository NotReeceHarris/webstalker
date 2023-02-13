import importlib

def check_packages(required_packages):
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    if len(missing) != 0:
        return False, missing
    else:
        return True, None

if __name__ == '__main__':

    from src.utils import status
    from src.utils import hero
    print(hero)

    required_packages = ['requests', 'matplotlib', 'bs4']
    all_installed, missing_package = check_packages(required_packages)

    if not all_installed:
        exit(f"{status['error']} The following {'packages are' if len(missing_package) > 1 else 'package is'} missing: {', '.join(missing_package)}")
    else:
        from src.main import main
        main()