import asyncio
import re
import subprocess
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dir_enumerate")


@mcp.tool()
async def dirb(target: str, wordlists: Optional[List[str]] = None, dirb_args: Optional[List[str]] = None) -> str:
    """
    Usage: dirb <url_base> [<wordlist_file(s)>] [options]

    Perform directory brute forcing using DIRB on the target URL.

    Args:
        target: The base URL to scan (e.g., http://example.com/).
        wordlists: A list of wordlist file paths. If None, use the default wordlist.
        dirb_args: Additional command-line arguments for dirb (e.g., ["-X", ".php"]).

    Classic Options:
        <url_base> : Base URL to scan.
        <wordlist_file(s)> : List of wordfiles (wordfile1,wordfile2,...).
        -X <extensions> : Append each word with given extensions.
        -i : Case-insensitive search.
        -r : Do not search recursively.
        -S : Silent mode (do not print tested words).

    Examples:
        dirb http://192.168.254.130/
        dirb http://192.168.254.130/ /usr/share/dirb/wordlists/common.txt
        dirb http://192.168.254.130/ /usr/share/dirb/wordlists/common.txt -X .php,.bak
    """
    if dirb_args is None:
        dirb_args = []

    if "-S" not in dirb_args:
        dirb_args.append("-S")

    if wordlists is None or len(wordlists) == 0:
        cmd = ["dirb", target] + dirb_args
    else:
        wordlist_str = ",".join(wordlists)
        cmd = ["dirb", target, wordlist_str] + dirb_args

    try:
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

        stdout_bytes, _ = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")

        return (
            f"{stdout}\nDirb completed successfully"
            if process.returncode == 0
            else f"Dirb failed with code {process.returncode}\nOutput:\n{stdout}"
        )

    except Exception as e:
        return f"Failed to execute Dirb: {str(e)}"


# @mcp.tool()
# async def dirsearch(target: str, dirsearch_options: Optional[List[str]] = None) -> str:
#     """
#         The user needs to input the target URL as "target". You need to read the following functions and parse the requirements. If necessary, you can add the following functions and corresponding parameters in "dirsearch_option". Analyze the output and solve the user's problem.
#         example:dirsearch -u 127.0.0.1s
#     Usage: dirsearch [-u|--url] target [-e|--extensions] extensions [options]

#     Options:
#       --version             show program's version number and exit
#       -h, --help            show this help message and exit

#       Mandatory:
#         -u URL, --url=URL   Target URL(s), can use multiple flags
#         -l PATH, --url-file=PATH
#                             URL list file
#         --stdin             Read URL(s) from STDIN
#         --cidr=CIDR         Target CIDR
#         --raw=PATH          Load raw HTTP request from file (use `--scheme` flag
#                             to set the scheme)
#         -s SESSION_FILE, --session=SESSION_FILE
#                             Session file
#         --config=PATH       Full path to config file, see 'config.ini' for example
#                             (Default: config.ini)

#       Dictionary Settings:
#         -w WORDLISTS, --wordlists=WORDLISTS
#                             Customize wordlists (separated by commas)
#         -e EXTENSIONS, --extensions=EXTENSIONS
#                             Extension list separated by commas (e.g. php,asp)
#         -f, --force-extensions
#                             Add extensions to the end of every wordlist entry. By
#                             default dirsearch only replaces the %EXT% keyword with
#                             extensions
#         -O, --overwrite-extensions
#                             Overwrite other extensions in the wordlist with your
#                             extensions (selected via `-e`)
#         --exclude-extensions=EXTENSIONS
#                             Exclude extension list separated by commas (e.g.
#                             asp,jsp)
#         --remove-extensions
#                             Remove extensions in all paths (e.g. admin.php ->
#                             admin)
#         --prefixes=PREFIXES
#                             Add custom prefixes to all wordlist entries (separated
#                             by commas)
#         --suffixes=SUFFIXES
#                             Add custom suffixes to all wordlist entries, ignore
#                             directories (separated by commas)
#         -U, --uppercase     Uppercase wordlist
#         -L, --lowercase     Lowercase wordlist
#         -C, --capital       Capital wordlist

#       General Settings:
#         -t THREADS, --threads=THREADS
#                             Number of threads
#         -r, --recursive     Brute-force recursively
#         --deep-recursive    Perform recursive scan on every directory depth (e.g.
#                             api/users -> api/)
#         --force-recursive   Do recursive brute-force for every found path, not
#                             only directories
#         -R DEPTH, --max-recursion-depth=DEPTH
#                             Maximum recursion depth
#         --recursion-status=CODES
#                             Valid status codes to perform recursive scan, support
#                             ranges (separated by commas)
#         --subdirs=SUBDIRS   Scan sub-directories of the given URL[s] (separated by
#                             commas)
#         --exclude-subdirs=SUBDIRS
#                             Exclude the following subdirectories during recursive
#                             scan (separated by commas)
#         -i CODES, --include-status=CODES
#                             Include status codes, separated by commas, support
#                             ranges (e.g. 200,300-399)
#         -x CODES, --exclude-status=CODES
#                             Exclude status codes, separated by commas, support
#                             ranges (e.g. 301,500-599)
#         --exclude-sizes=SIZES
#                             Exclude responses by sizes, separated by commas (e.g.
#                             0B,4KB)
#         --exclude-text=TEXTS
#                             Exclude responses by text, can use multiple flags
#         --exclude-regex=REGEX
#                             Exclude responses by regular expression
#         --exclude-redirect=STRING
#                             Exclude responses if this regex (or text) matches
#                             redirect URL (e.g. '/index.html')
#         --exclude-response=PATH
#                             Exclude responses similar to response of this page,
#                             path as input (e.g. 404.html)
#         --skip-on-status=CODES
#                             Skip target whenever hit one of these status codes,
#                             separated by commas, support ranges
#         --min-response-size=LENGTH
#                             Minimum response length
#         --max-response-size=LENGTH
#                             Maximum response length
#         --max-time=SECONDS  Maximum runtime for the scan
#         --exit-on-error     Exit whenever an error occurs

#       Request Settings:
#         -m METHOD, --http-method=METHOD
#                             HTTP method (default: GET)
#         -d DATA, --data=DATA
#                             HTTP request data
#         --data-file=PATH    File contains HTTP request data
#         -H HEADERS, --header=HEADERS
#                             HTTP request header, can use multiple flags
#         --header-file=PATH  File contains HTTP request headers
#         -F, --follow-redirects
#                             Follow HTTP redirects
#         --random-agent      Choose a random User-Agent for each request
#         --auth=CREDENTIAL   Authentication credential (e.g. user:password or
#                             bearer token)
#         --auth-type=TYPE    Authentication type (basic, digest, bearer, ntlm, jwt,
#                             oauth2)
#         --cert-file=PATH    File contains client-side certificate
#         --key-file=PATH     File contains client-side certificate private key
#                             (unencrypted)
#         --user-agent=USER_AGENT
#         --cookie=COOKIE

#       Connection Settings:
#         --timeout=TIMEOUT   Connection timeout
#         --delay=DELAY       Delay between requests
#         --proxy=PROXY       Proxy URL (HTTP/SOCKS), can use multiple flags
#         --proxy-file=PATH   File contains proxy servers
#         --proxy-auth=CREDENTIAL
#                             Proxy authentication credential
#         --replay-proxy=PROXY
#                             Proxy to replay with found paths
#         --tor               Use Tor network as proxy
#         --scheme=SCHEME     Scheme for raw request or if there is no scheme in the
#                             URL (Default: auto-detect)
#         --max-rate=RATE     Max requests per second
#         --retries=RETRIES   Number of retries for failed requests
#         --ip=IP             Server IP address

#       Advanced Settings:
#         --crawl             Crawl for new paths in responses

#       View Settings:
#         --full-url          Full URLs in the output (enabled automatically in
#                             quiet mode)
#         --redirects-history
#                             Show redirects history
#         --no-color          No colored output
#         -q, --quiet-mode    Quiet mode

#       Output Settings:
#         -o PATH, --output=PATH
#                             Output file
#         --format=FORMAT     Report format (Available: simple, plain, json, xml,
#                             md, csv, html, sqlite)
#         --log=PATH          Log file

#     """
#     if dirsearch_options is None:
#         dirsearch_options = [""]
#     ##实际命令
#     cmd = "dirsearch -u " + target + " " + " ".join(dirsearch_options)

#     try:
#         result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#         # 匹配输出文件路径

#         output_file_match = re.search(r"Output File: (.*)", result.stdout)
#         if output_file_match:
#             output_file = output_file_match.group(1).strip()
#             cmd = f"cat {output_file}"
#             result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#             return result.stdout
#         else:
#             print("Cant match output file")
#             return result.stdout
#         # 读取输出文件内容

#     except subprocess.CalledProcessError as e:
#         return str(e.stderr)


if __name__ == "__main__":
    mcp.run(transport="stdio")
