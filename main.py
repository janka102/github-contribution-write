#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
import random
import subprocess
import sys
from time import sleep

ASCII_PRINTABLE_FIRST = 32  # space
ASCII_PRINTABLE_LAST = 126  # tilde
ESC = chr(0x1B)


def main():
    parser = argparse.ArgumentParser(
        description="Write text into GitHub's contribution graph by creating a bunch of commits at specific times"
    )

    parser.add_argument(
        "-c",
        "--min-commits",
        help="The minimum commits for a day (default 30)",
        type=int,
        default=30,
    )
    parser.add_argument(
        "-C",
        "--max-commits",
        help="The maximum commits for a day (default 35)",
        type=int,
        default=35,
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        help="Do not actually create the commits",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--invert",
        help="Invert the text to be light text on dark background",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--preview",
        help="Preview the message in the terminal",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--start",
        help="The date to start at, in YYYY-MM-DD format",
        type=str,
        default=(datetime.today() - timedelta(weeks=52)).isoformat(),
    )

    parser.add_argument("message", help="The text to write", nargs="+")

    args = parser.parse_args()

    message = " ".join(args.message)

    if len(message) == 0:
        parser.print_usage()
        eprint("Empty message is invalid")
        sys.exit(1)

    if args.min_commits < 0:
        parser.print_usage()
        eprint("MIN_COMMITS must be at least 0")
        sys.exit(1)

    if args.max_commits < 1:
        parser.print_usage()
        eprint("MAX_COMMITS must be at least 1")
        sys.exit(1)

    if args.min_commits > args.max_commits:
        parser.print_usage()
        eprint(
            f"MIN_COMMITS ({args.min_commits}) cannot be more than MAX_COMMITS ({args.max_commits})"
        )
        sys.exit(1)

    invalid = []

    for char in message:
        digit = ord(char)
        if digit < ASCII_PRINTABLE_FIRST or digit > ASCII_PRINTABLE_LAST:
            invalid.append("0x{:02X}".format(digit))

    if len(invalid) > 0:
        parser.print_usage()
        eprint(f"Unsupported characters in message: {' '.join(invalid)}")
        sys.exit(1)

    font = get_font()

    grid = []
    for row in range(7):
        row_text = "."

        for char in message:
            digit = ord(char) - ASCII_PRINTABLE_FIRST
            font_letter = font[digit]
            row_text += font_letter[row] + "."

        if args.invert:
            row_text = "".join(["#" if c == "." else "." for c in row_text])

        grid.append(row_text)

    num_days = len(grid) * len(grid[0])
    beginning = datetime.fromisoformat(args.start).replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    # start on Sunday
    beginning = beginning - timedelta(days=(beginning.weekday() + 1) % 7)
    end = beginning + timedelta(days=num_days - 1)

    print(f"Starting on {beginning.strftime('%a %b %d %H:%M:%S %Z %Y')}")
    print(f"Ending on   {end.strftime('%a %b %d %H:%M:%S %Z %Y')}")

    if args.preview:
        # make room for the preview lines
        for _ in range(len(grid)):
            print("")

    for day in range(num_days):
        y = day % 7
        x = day // 7
        row = grid[y]
        char = row[x]
        the_date = (beginning + timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"\r{the_date} {progress(day * 100 / num_days)}",
            end="",
        )

        if char == ".":
            continue

        if not args.dry_run:
            commits_diff = args.max_commits - args.min_commits + 1
            num_commits = args.min_commits + random.randrange(commits_diff)

            for _ in range(num_commits):
                subprocess.run(
                    [
                        "git",
                        "commit",
                        "--allow-empty",
                        f"--date={the_date}",
                        "--message",
                        the_date,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        else:
            # artificial deplay just to show progress working
            sleep(0.002)

        if args.preview:
            print("\r", end="")
            cursor_up(7 - y)
            cursor_right(x)
            print(char, end="")
            cursor_down(7 - y)

    print(
        f"\r{the_date} {progress(100)}",
        end="",
    )


def progress(percent):
    bar = ""
    for i in range(25):
        if i * 4 <= percent:
            bar += "="
        else:
            bar += " "

    return f"[{bar}] {int(percent)}%"


def get_font():
    font = [
        """
        ..
        ..
        ..
        ..
        ..
        ..
        ..
        """,
        """
        .
        #
        #
        #
        .
        #
        .
        """,
        """
        ...
        #.#
        #.#
        ...
        ...
        ...
        ...
        """,
        """
        .....
        .#.#.
        #####
        .#.#.
        #####
        .#.#.
        .....
        """,
        """
        ..#..
        .####
        #.#..
        .###.
        ..#.#
        ####.
        ..#..
        """,
        """
        .....
        ##..#
        ##.#.
        ..#..
        .#.##
        #..##
        .....
        """,
        """
        .##..
        #..#.
        .#...
        .##..
        #.#.#
        #..##
        .##.#
        """,
        """
        .
        #
        #
        .
        .
        .
        .
        """,
        """

        .#
        #.
        #.
        #.
        #.
        #.
        .#
        """,
        """

        #.
        .#
        .#
        .#
        .#
        .#
        #.
        """,
        """
        ...
        .#.
        ###
        .#.
        ...
        ...
        ...
        """,
        """
        ...
        ...
        .#.
        ###
        .#.
        ...
        ...
        """,
        """
        .
        .
        .
        .
        .
        #
        #
        """,
        """
        ...
        ...
        ...
        ###
        ...
        ...
        ...
        """,
        """
        .
        .
        .
        .
        .
        #
        .
        """,
        """
        .....
        ....#
        ...#.
        ..#..
        .#...
        #....
        .....
        """,
        """
        ....
        .##.
        #..#
        #..#
        #..#
        .##.
        ....
        """,
        """
        ...
        .#.
        ##.
        .#.
        .#.
        ###
        ...
        """,
        """
        ....
        .##.
        #..#
        ..#.
        #...
        ####
        ....
        """,
        """
        ....
        ###.
        ...#
        .##.
        ...#
        ###.
        ....
        """,
        """
        ....
        ..#.
        .##.
        #.#.
        ####
        ..#.
        ....
        """,
        """
        ....
        ####
        #...
        ###.
        ...#
        ###.
        ....
        """,
        """
        ....
        .##.
        #...
        ###.
        #..#
        .##.
        ....
        """,
        """
        ....
        ####
        ...#
        ..#.
        .#..
        #...
        ....
        """,
        """
        ....
        .##.
        #..#
        .##.
        #..#
        .##.
        ....
        """,
        """
        ....
        .##.
        #..#
        .###
        ...#
        ..#.
        ....
        """,
        """
        .
        .
        #
        .
        #
        .
        .
        """,
        """
        .
        .
        #
        .
        #
        #
        .
        """,
        """
        ...
        ..#
        .#.
        #..
        .#.
        ..#
        ...
        """,
        """
        ...
        ...
        ###
        ...
        ###
        ...
        ...
        """,
        """
        ...
        #..
        .#.
        ..#
        .#.
        #..
        ...
        """,
        """
        ....
        .##.
        ...#
        ..#.
        ....
        ..#.
        ....
        """,
        """
        .....
        .###.
        #.#.#
        #.#.#
        #.###
        .##..
        .....
        """,
        """
        ....
        .##.
        #..#
        ####
        #..#
        #..#
        ....
        """,
        """
        ....
        ###.
        #..#
        ###.
        #..#
        ###.
        ....
        """,
        """
        ....
        .###
        #...
        #...
        #...
        .###
        ....
        """,
        """
        ....
        ##..
        #.#.
        #..#
        #.#.
        ##..
        ....
        """,
        """
        ....
        ####
        #...
        ###.
        #...
        ####
        ....
        """,
        """
        ....
        ####
        #...
        ###.
        #...
        #...
        ....
        """,
        """
        ....
        .###
        #...
        #.##
        #..#
        .###
        ....
        """,
        """
        ....
        #..#
        #..#
        ####
        #..#
        #..#
        ....
        """,
        """
        ...
        ###
        .#.
        .#.
        .#.
        ###
        ...
        """,
        """
        ....
        ...#
        ...#
        ...#
        #..#
        .##.
        ....
        """,
        """
        ....
        #..#
        #.#.
        ##..
        #.#.
        #..#
        ....
        """,
        """
        ....
        #...
        #...
        #...
        #...
        ####
        ....
        """,
        """
        .....
        .#.#.
        #.#.#
        #.#.#
        #...#
        #...#
        .....
        """,
        """
        .....
        #...#
        ##..#
        #.#.#
        #..##
        #...#
        .....
        """,
        """
        ....
        .##.
        #..#
        #..#
        #..#
        .##.
        ....
        """,
        """
        ....
        ###.
        #..#
        ###.
        #...
        #...
        ....
        """,
        """
        ....
        .##.
        #..#
        #..#
        #.##
        .##.
        ...#
        """,
        """
        ....
        ###.
        #..#
        ###.
        #.#.
        #..#
        ....
        """,
        """
        ....
        .###
        #...
        .##.
        ...#
        ###.
        ....
        """,
        """
        ...
        ###
        .#.
        .#.
        .#.
        .#.
        ...
        """,
        """
        ....
        #..#
        #..#
        #..#
        #..#
        .##.
        ....
        """,
        """
        ....
        #..#
        #..#
        #..#
        #.#.
        .#..
        ....
        """,
        """
        .....
        #...#
        #...#
        #.#.#
        #.#.#
        .#.#.
        .....
        """,
        """
        .....
        #...#
        .#.#.
        ..#..
        .#.#.
        #...#
        .....
        """,
        """
        ...
        #.#
        #.#
        .#.
        .#.
        .#.
        ...
        """,
        """
        ....
        ####
        ..#.
        .#..
        #...
        ####
        ....
        """,
        """
        ##
        #.
        #.
        #.
        #.
        #.
        ##
        """,
        """
        .....
        #....
        .#...
        ..#..
        ...#.
        ....#
        .....
        """,
        """
        ##
        .#
        .#
        .#
        .#
        .#
        ##
        """,
        """
        ...
        .#.
        #.#
        ...
        ...
        ...
        ...
        """,
        """
        ...
        ...
        ...
        ...
        ...
        ###
        ...
        """,
        """
        ..
        #.
        .#
        ..
        ..
        ..
        ..
        """,
        """
        ....
        .##.
        ...#
        .###
        #..#
        .###
        ....
        """,
        """
        ....
        #...
        #...
        ###.
        #..#
        ###.
        ....
        """,
        """
        ...
        ...
        ...
        .##
        #..
        .##
        ...
        """,
        """
        ....
        ...#
        ...#
        .###
        #..#
        .###
        ....
        """,
        """
        ....
        ....
        .##.
        ####
        #...
        .###
        ....
        """,
        """
        ....
        ..##
        .#..
        ###.
        .#..
        .#..
        ....
        """,
        """
        ....
        ....
        .###
        #..#
        .###
        ...#
        .##.
        """,
        """
        ....
        #...
        #...
        ###.
        #..#
        #..#
        ....
        """,
        """
        .
        #
        .
        #
        #
        #
        .
        """,
        """
        ...
        ..#
        ...
        ..#
        ..#
        ..#
        ##.
        """,
        """
        ...
        #..
        #..
        #.#
        ##.
        #.#
        ...
        """,
        """
        .
        #
        #
        #
        #
        #
        .
        """,
        """
        .....
        .....
        .....
        .#.#.
        #.#.#
        #...#
        .....
        """,
        """
        ....
        ....
        ....
        .##.
        #..#
        #..#
        ....
        """,
        """
        ....
        ....
        ....
        .##.
        #..#
        .##.
        ....
        """,
        """
        ....
        ....
        .##.
        #..#
        ###.
        #...
        #...
        """,
        """
        ....
        ....
        .##.
        #..#
        .###
        ...#
        ...#
        """,
        """
        ...
        ...
        ...
        .##
        #..
        #..
        ...
        """,
        """
        ....
        ....
        .###
        #...
        ..##
        ###.
        ....
        """,
        """
        ...
        .#.
        .#.
        ###
        .#.
        .#.
        ...
        """,
        """
        ....
        ....
        ....
        #..#
        #..#
        .##.
        ....
        """,
        """
        ....
        ....
        ....
        #..#
        #.#.
        .#..
        ....
        """,
        """
        .....
        .....
        .....
        #...#
        #.#.#
        .#.#.
        .....
        """,
        """
        ...
        ...
        ...
        #.#
        .#.
        #.#
        ...
        """,
        """
        ...
        ...
        #.#
        .##
        ..#
        .#.
        ...
        """,
        """
        ...
        ...
        ###
        .#.
        #..
        ###
        ...
        """,
        """
        .##
        .#.
        .#.
        #..
        .#.
        .#.
        .##
        """,
        """
        .
        #
        #
        #
        #
        #
        .
        """,
        """
        ##.
        .#.
        .#.
        ..#
        .#.
        .#.
        ##.
        """,
        """
        ......
        ......
        .##..#
        #..##.
        ......
        ......
        ......
            """,
    ]

    return [[row.strip() for row in char.split()] for char in font]


def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def cursor_up(n):
    if n > 0:
        print(f"{ESC}[{n}A", end="")


def cursor_down(n):
    if n > 0:
        print(f"{ESC}[{n}B", end="")


def cursor_right(n):
    if n > 0:
        print(f"{ESC}[{n}C", end="")


main()
