#!/usr/bin/env python3

## Copyright (C) 2022 David Miguel Susano Pinto <carandraug+dev@gmail.com>
##
## Copying and distribution of this file, with or without modification,
## are permitted in any medium without royalty provided the copyright
## notice and this notice are preserved.  This file is offered as-is,
## without any warranty.

## List the functions in a Matlab package.
##
## For example:
##
##    # List image processing package functions
##    list-matlab-package-functions.py images
##
##    # List signal processing package functions
##    list-matlab-package-functions.py signal

import argparse
import sys
import typing
import urllib.request
import xml.etree.ElementTree as ET


_PRINT_FQCN = True


def fetch_reference_list(pkg_name: str) -> ET.Element:
    url = (
        "https://uk.mathworks.com/help/%s/referencelist_function_alpha.xml"
        % pkg_name
    )
    with urllib.request.urlopen(url) as response:
        html = response.read()
    return ET.fromstring(html)


def has_dot_in_target_basename(target: str) -> bool:
    assert (
        target.startswith("ref/")
        and target.find("/", 4) == -1
        and target.endswith(".html")
    )
    return target.find(".", 4, -5) > -1


def parse_fq_class_name(target: str, name: str) -> str:
    # "target" is the url link, so everything is lower case.  "name"
    # shuld have the class name with correct capitalisation, so fix at
    # least that.
    fqcn_lc = target[4:-5]
    return fqcn_lc[:-len(name)] + name


def deep_search_for_functions(
    element: ET.Element,
) -> typing.List[str]:
    functions: typing.List[str] = []

    if element.tag == "{https://www.mathworks.com/help/ref/data}ref":
        assert (
            element.attrib
            and "name" in element.attrib
            and "target" in element.attrib
        )

        # "name" is the function or class name.  In the case of a
        # class, it is *not* the fully qualified class name.  For
        # classdef style classes we would rather use the FQCN since
        # that's what the user uses, but that's not the case for the
        # old style @class such as many of the control package
        # classes.  Set _PRINT_FQCN to control that.
        name = element.attrib["name"]
        if _PRINT_FQCN:
            target = element.attrib["target"]
            if has_dot_in_target_basename(target):
                functions.append(parse_fq_class_name(target, name))
            else:
                functions.append(name)
        else:
            functions.append(name)

    for children in list(element):
        functions += deep_search_for_functions(children)

    return functions


def print_for_octave(functions: typing.List[str]) -> None:
    # The list of functions was generated from a list of functions and
    # classes already in alphabetic order.  However, in the case of
    # classes we may have now FQCN so sort them again so methods and
    # classes appear together and make it easier to manually curate
    # later.

    cur_pos = 0
    print("    case {", end="")
    cur_pos = 10
    for function in sorted(functions):
        # Will print at most '"functio-name", ...'
        chars_to_print = len(function) + 7
        if cur_pos + chars_to_print > 79:
            print("...")
            print("          ", end="")
            cur_pos = 10
        print('"%s"' % function, end=", ")
        cur_pos += len(function) + 4
    print("}")


def main(argv: typing.List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "pkg_name",
        help="package name as appears on Matlab URL",
    )
    args = parser.parse_args(argv[1:])

    xml_element = fetch_reference_list(args.pkg_name)
    functions = deep_search_for_functions(xml_element)
    print_for_octave(functions)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
