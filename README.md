# checkhtml.py
This script is useful for checking the indentation an unclosed tag on a html.

## Running the tool
Running the script by using python3 and the [html-path]:
```
python3 <script-path> <html-path>
```
For example, if you are located in the script folder:
```
python3 checkhtml.py <html-path>
```

## Unclosed tags
The tool finds where are located the unclosed tags.

The following self-closing tags are pre filtered in order to avoid the flag of the expected unclosed tag:
* area
* base
* br
* col
* embed
* hr
* img
* input
* link
* meta
* param
* source
* track
* wbr
* ! (comment)

# Indentation errors
This tool use two indentation criteria:
1) opening tag and closing tag are in the same line.
2) opening tag and closing tag are not in the same line but both have the the same indentation.
```
✅ Examples of Good indentation
01--<div><p>content</p></div>
02
03--<div>
04----<p>content</p>
05--</div>
06
07--<div>
08----<p>
09------content
10----</p>
11--</div>
12
❌ Examples of Bad indentation
01--<div><p>
02----content</p></div>
03
04----<div>
05----<p>content</p>
06--</div>
07
08--<div>
09----<p>
10------content
11----</p>
12----</div>
13
```