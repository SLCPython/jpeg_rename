#!/usr/bin/env python

from __future__ import print_function
import argparse
import glob
import os
import re
import sys
import PIL
from PIL.ExifTags import TAGS
from PIL import Image


EXTENSIONS = ['JPG', 'jpg', 'jpeg']


def read_exif_data(workdir, old_fn):
    """Read EXIF data from file. Convert to Python dict. Return dict."""

    # XXX: We already know file exists 'cuz we found it.
    img = Image.open(os.path.join(workdir, old_fn))
    info = img._getexif()

    exif_data ={}
    if info is not None:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            exif_data[decoded] = value

    return exif_data


def get_new_fn(old_fn, exif_data):
    """Generate new filename from old_fn EXIF data if possible. Even if not
    possible, lowercase old_fn and normalize file extension.

    Arguments:
        Python dict: EXIF data

    Returns:
        str: Filename derived from EXIF data.

    >>> exif_data = {}
    >>> old_fn = 'abc123.jpg'
    >>> exif_data['DateTimeOriginal'] = '2014:08:16 06:20:30'
    >>> get_new_fn(old_fn, exif_data)
    '20140816_062030.jpg'

    """

    # Start with EXIF DateTimeOriginal
    try:
        new_fn = exif_data['DateTimeOriginal']
    except KeyError:
        new_fn = None

    # If this pattern does not strictly match then keep original name.
    # YYYY:MM:DD HH:MM:SS
    if (new_fn and not
            re.match(r'^\d{4}:\d\d:\d\d \d\d:\d\d:\d\d$', new_fn)):
        # Setup for next step.
        new_fn = None

    # Don't assume exif tag exists. If it does not, keep original filename.
    # Lowercase filename base and extension
    if new_fn is None:
        new_fn = old_fn.lower()
        new_fn = re.sub(r'.jpeg$', r'.jpg', new_fn)
    else:
        new_fn = "{0}.jpg".format(new_fn)

    # XXX: One may argue that the next step should be an 'else' clause of the
    # previous 'if' statement. But the intention here is to clean up just a bit
    # even if we're not really renaming the file. Windows doesn't like colons
    # in filenames.

    # Rename using exif DateTimeOriginal
    new_fn = re.sub(r':', r'', new_fn)
    new_fn = re.sub(r' ', r'_', new_fn)

    return new_fn


def move(old_fn, new_fn):
    """Move old_fn to new_fn."""

    print( "Really moving the files: {0} ==> {1}".format(
        os.path.basename(old_fn), os.path.basename(new_fn)))


def init_file_map(workdir):
    """Read the work directory looking for files with extensions defined in the
    EXTENSIONS constant. Note that this could use a more elaborate magic
    number mechanism that would be cool.
    """

    # Dict with old_fn ==> new_fn mapping.
    file_map = {}

    # Initialize file_map dict.
    # Need to look for *.JPG, *.jpg, and *.jpeg files for consideration.
    for extension in EXTENSIONS:
        for filename in glob.glob(os.path.join(workdir,
                '*.{0}'.format(extension))):
            old_fn = os.path.basename(filename)
            exif_data = read_exif_data(workdir, old_fn)
            file_map[old_fn] = get_new_fn(old_fn, exif_data)

    return file_map


def process_file_map(workdir, file_map, clobber, move_func=move):
    """Iterate through the Python dict that maps old filenames to new
    filenames. Move the file if Simon sez.

    Args: Takes working directory, file map, clobber, and move function.
    Returns: None

    >>> file_map = {'IMG0332.JPG': '20140818_20238345.jpg'}
    >>> def move_func(old_fn, new_fn): pass
    ...
    >>> process_file_map('.', file_map, True, move_func)
    >>>

    """

    for old_fn, new_fn in file_map.iteritems():
        try:
            if clobber and move_func:
                move_func(os.path.join(workdir, old_fn),
                        os.path.join(workdir, new_fn))
        except Exception as e:
            print("{0}".format(e.message), file=sys.stderr)
            break


def process_all_files(workdir=None, clobber=None):
    """Manage the entire process of gathering data and renaming files."""

    if workdir is None:
        workdir = os.path.dirname(os.path.abspath(__file__))

    if not os.path.exists(workdir):
        print("Directory {0} does not exist. Exiting.",format(workdir),
                file=sys.stderr)
        sys.exit(1)

    if not os.access(workdir, os.W_OK):
        print("Directory {0} is not writable. Exiting.".format(workdir),
                file=sys.stderr)
        sys.exit(1)

    if clobber is None:
        clobber = False

    file_map = init_file_map(workdir)
    process_file_map(workdir, file_map, clobber)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--clobber",
            help="Really, Simon sez rename the files!", action="store_true")
    parser.add_argument("-d", "--directory",
            help="Read files from this directory.")
    args = parser.parse_args()
    process_all_files(workdir=args.directory, clobber=args.clobber)
