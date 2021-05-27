#!/usr/bin/python3

from datetime import date, datetime
from hashlib import sha256

from dateutil.relativedelta import relativedelta


def empty_strings_to_none(dictionary):
    new_dictionary = {}
    for key, value in dictionary.items():
        if value == "":
            new_dictionary[key] = None
        else:
            new_dictionary[key] = value
    return new_dictionary


def current_month_num():
    """Returns the current month number as an integer."""
    return int(datetime.now().strftime("%m"))


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


def last_day_of_month(input_date):
    next_month = input_date + relativedelta(months=1)
    first_day_of_next_month = date(next_month.year, next_month.month, 1)
    return first_day_of_next_month - relativedelta(days=1)


def month_input_to_date(month_input, set_to_last_day=False):
    if month_input is None:
        return None
    elif set_to_last_day is False:
        return datetime.strptime(month_input, "%Y-%m").date()
    else:
        return last_day_of_month(
            datetime.strptime(month_input, "%Y-%m").date()
        )


def date_to_month_input(date_obj):
    if date_obj is None:
        return None
    else:
        return date_obj.strftime("%Y-%m")


def month_count(start_date, end_date):
    count = 0
    one_month = relativedelta(months=1)

    if start_date > end_date:
        return 0

    while True:
        count += 1
        if (
            start_date.year == end_date.year
            and start_date.month == end_date.month
        ):
            break
        else:
            start_date += one_month

    return count


def checkbox_to_boolean(value):
    if value == "on":
        return True
    else:
        return False


def hash(value, salt=""):
    hashed_value = sha256((value + salt).encode()).hexdigest()
    return hashed_value


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
    12: "December",
}
