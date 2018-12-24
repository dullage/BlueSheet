#!/usr/bin/python3
import math

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])  # noqa


def empty_strings_to_none(dictionary):
    new_dictionary = {}
    for key, value in dictionary.items():
        if value == "":
            new_dictionary[key] = None
        else:
            new_dictionary[key] = value
    return new_dictionary
