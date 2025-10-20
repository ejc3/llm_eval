# Tool: ls

## Overview
List directory contents (bare list), one entry per line, lexicographic, no colors, no trailing slashes.

## Examples
$ ls
README.md
jobs
src

$ ls jobs
42.log
43.log

$ ls missing
ls: cannot access 'missing': No such file or directory

## Notes
- Flags like `-l` or `-a` may be used; when unspecified, default to bare listing.

## Fallback
If unsure, print exactly:
SIM-UNKNOWN::ls::insufficient-context
