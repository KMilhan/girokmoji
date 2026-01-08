#!/usr/bin/env python3
import os
import sys


def main() -> None:
    if len(sys.argv) < 2:
        sys.stderr.write("zig-cc-wrapper: missing compiler argument\n")
        sys.exit(1)

    compiler = sys.argv[1]
    args = []
    it = iter(sys.argv[2:])
    for arg in it:
        if arg == "-Xlinker":
            nxt = next(it, "")
            if nxt.startswith("--dependency-file="):
                continue
            args.extend([arg, nxt])
            continue
        if arg.startswith("--dependency-file="):
            continue
        args.append(arg)

    os.execvp(compiler, [compiler, *args])


if __name__ == "__main__":
    main()
