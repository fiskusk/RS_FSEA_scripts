import sys

def version_check():
    version_info = sys.version_info
    if version_info < (3, 9) or version_info >= (3, 10) :
        version_info = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        string = f"You're executing the script with Python {version_info}. Execute the script with Python 3.9"
        print(string)
        exit(0)