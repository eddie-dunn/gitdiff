#!/usr/bin/env python3
"""
Check the git diff and generate a diff viewer in the browser.

Depends on git.
"""

import textwrap
import argparse
import os
import subprocess
import webbrowser
import html
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from string import Template

EDITOR_URI = "vscode://file/"
OPEN_IN_BROWSER = True
PORT = 8000

PAGE = "http://localhost"
URL = f"{PAGE}:{PORT}"
DIR = "/tmp/gitdiff"


class ServerHandler(SimpleHTTPRequestHandler):
    directory = DIR


def run_server(*, server_dir, port, server_class=HTTPServer, handler=ServerHandler):
    os.chdir(server_dir)
    server_address = ("", port)
    print("Serving files from", handler.directory)
    httpd = server_class(server_address, handler)
    httpd.serve_forever()


def setup_dir():
    try:
        os.mkdir(DIR)
    except:
        pass


def write_html(diff):
    HTML_TEMPLATE = Template(
        """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />

    <title>Diff viewer</title>
    <link rel="stylesheet" href="css/main.css" />
  </head>

  <body>
    <h1>Diff viewer</h1>
    <div class="diff-box">
      $gitdiff
    </div>
  </body>

  <style>
    body {
      display: flex;
      flex-direction: column;
      max-width: 100ch;
      margin: auto;
      padding: 1rem;
    }

    .diff-box {
        border: 1px solid #ccc;
        padding: 1rem;
        font-family: monospace;
        white-space: pre;
        display: flex;
        flex-direction: column;
        overflow: auto;
    }

    .red {
        color: red;
    }

    .green {
        color: green;
    }
  </style>
</html>
    """
    )
    with open(f"{DIR}/index.html", "w") as f:
        f.write(HTML_TEMPLATE.substitute(gitdiff=str(diff)))


def generate_diff(target, source="HEAD"):
    cmd = ["git", "diff", f"{source}..{target}"]
    print(" ".join(cmd))
    out = subprocess.run(cmd, capture_output=True, encoding="utf8")
    return html.escape(out.stdout)


def parse_diff(diff, editor_uri):
    # print("orig", diff)
    parsed = []
    filename = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            filename = line.split("/", 1)[-1]
            href = f"{editor_uri}/{os.path.abspath(filename)}"
            link = f'<a href="{href}">{line}</a>'
            # print(link)
            parsed.append(link)
        elif line.startswith("@@"):
            offset_list = line.split("@@")
            offset_string = offset_list[1].strip()
            end_of_line = offset_list[-1].lstrip()
            line_number = offset_string.split("+")[-1].split(",")[0].strip()
            href = f"{editor_uri}/{os.path.abspath(filename)}:{line_number}"
            link = f'<a href="{href}">@@ {offset_string} @@</a> {end_of_line}'
            # print(link)
            parsed.append(f"<div>{link}</div>")
            pass
        elif line.startswith("-"):
            diff_removed = f'<div class="red">{line}</div>'
            parsed.append(diff_removed)
        elif line.startswith("+"):
            diff_added = f'<div class="green">{line}</div>'
            parsed.append(diff_added)
        else:
            parsed.append(f'<div class="grey">{line}</div>')

    result = "\n".join(parsed)
    return result


def main(*, target, source, open_in_browser, editor_uri, port):
    setup_dir()

    parsed_diff = parse_diff(generate_diff(target, source), editor_uri)
    write_html(parsed_diff)
    if open_in_browser:
        # webbrowser.open_new(URL) # open in new window
        webbrowser.open(URL, 2)  # open in new tab
    else:
        print("Open in browser:", URL)
    run_server(server_dir=DIR, port=port)


def parseArgs():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """
            Check the git diff and generate a diff viewer in the browser.

            Depends on git."""
        )
    )
    parser.add_argument(
        "target", help="SHA1/branch to diff against", default="HEAD^", nargs="?"
    )
    parser.add_argument(
        "source", help="SHA1/branch to diff from", default="HEAD", nargs="?"
    )
    parser.add_argument(
        "--editor-uri",
        help="Editor uri for opening files",
        default=EDITOR_URI,
    )
    parser.add_argument(
        "--no-browser",
        help="Prevent automatically opening diff in browser",
        action="store_true",
        default=not OPEN_IN_BROWSER,
    )
    parser.add_argument("-p", "--port", help="Port to run server on", default=PORT)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parseArgs()
    main(
        target=args.target,
        source=args.source,
        open_in_browser=not args.no_browser,
        editor_uri=args.editor_uri,
        port=args.port,
    )
    pass
