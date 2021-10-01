#!/usr/bin/env python3
"""
Check the git diff and generate a diff viewer in the browser.

Depends on git.
"""

# import textwrap  # use dedent?
import os
import subprocess
import webbrowser
import html
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from string import Template

# region Constants
EDITOR_URL = "vscode://file/"
OPEN_IN_BROWSER = True
PORT = 8000
PAGE = "http://localhost"
URL = f"{PAGE}:{PORT}"
DIR = "/tmp/gitdiff"
# endregion Constants


class ServerHandler(SimpleHTTPRequestHandler):
    directory = DIR


def run_server(server_dir, server_class=HTTPServer, handler=ServerHandler):
    os.chdir(server_dir)
    server_address = ("", PORT)
    print(handler.directory)
    httpd = server_class(server_address, handler)
    httpd.serve_forever()


def main():
    setup_dir()
    print(URL)
    parsed_diff = parse_diff(generate_diff())
    write_html(parsed_diff)
    if OPEN_IN_BROWSER:
        # webbrowser.open_new(URL) # open in new window
        webbrowser.open(URL, 2)  # open in new tab
    run_server(DIR)


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


def generate_diff():
    out = subprocess.run(["git", "diff"], capture_output=True, encoding="utf8")
    return html.escape(out.stdout)


def parse_diff(diff):
    # print("orig", diff)
    parsed = []
    filename = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            filename = line.split("/", 1)[-1]
            href = f"{EDITOR_URL}/{os.path.abspath(filename)}"
            link = f'<a href="{href}">{line}</a>'
            print(link)
            parsed.append(link)
        elif line.startswith("@@"):
            offset_list = line.split("@@")
            offset_string = offset_list[1].strip()
            end_of_line = offset_list[-1].lstrip()
            line_number = offset_string.split("+")[-1].split(",")[0].strip()
            href = f"{EDITOR_URL}/{os.path.abspath(filename)}:{line_number}"
            link = f'<a href="{href}">@@ {offset_string} @@</a> {end_of_line}'
            print(link)
            parsed.append(f"<div>{link}</div>")
            pass
        elif line.startswith("-"):
            # line = line.replace("-", "<del>-</del>")
            diff_removed = f'<div class="red">{line}</div>'
            parsed.append(diff_removed)
        elif line.startswith("+"):
            # line = line.replace("+", "<ins>+</ins>")
            diff_added = f'<div class="green">{line}</div>'
            parsed.append(diff_added)
        else:
            parsed.append(f'<div class="grey">{line}</div>')

    result = "\n".join(parsed)
    return result


if __name__ == "__main__":
    main()
    # test = parse_diff(generate_diff())
    pass
