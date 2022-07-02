#!/usr/bin/env python3

import argparse
import jsonpickle

from structures import *

def main() -> int:
    parser = argparse.ArgumentParser(description='Parse Zync Ultrascale+ Boot Image.')
    parser.add_argument('--boot_image_bin', required=True, help='Path to the .bin boot image.')
    parser.add_argument('--parsed_json', required=True, help='Path to where the parsed output will be written to.')
    args = parser.parse_args()

    with open(args.boot_image_bin, 'rb') as f:
        bin = f.read()
    
    image = Image(bin)

    serialized_image = jsonpickle.encode(image)

    with open(args.parsed_json, 'w') as f:
        f.write(serialized_image)


if __name__ == '__main__':
    raise SystemExit(main())