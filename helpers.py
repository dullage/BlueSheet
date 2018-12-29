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


demo_starling_account = {
    "effective_balance": 78.63,
    "savings_goals": {
        "1": {
            "name": "Holiday",
            "total_saved_minor_units": 10345
        },
        "2": {
            "name": "Wedding",
            "total_saved_minor_units": 2344
        },
        "3": {
            "name": "Christmas",
            "total_saved_minor_units": 9876
        }
    }
}

months = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}


def next_month(current_month):
    if current_month == 12:
        return 1
    else:
        return current_month + 1


def previous_month(current_month):
    if current_month == 1:
        return 12
    else:
        return current_month - 1
