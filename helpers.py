#!/usr/bin/python3

import math
from datetime import date, datetime
from hashlib import sha256

from dateutil.relativedelta import relativedelta

ordinal = lambda n: "%d%s" % (
    n,
    "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
)  # noqa


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


def weekdays_in_range(weekday_to_count, start_date, end_date):
    one_day = relativedelta(days=1)

    weekday_count = 0
    loop_date = start_date
    while loop_date <= end_date:
        if loop_date.weekday() == weekday_to_count:
            weekday_count += 1
        loop_date += one_day

    return weekday_count


def first_day_of_month(input_date):
    return date(input_date.year, input_date.month, 1)


def last_day_of_month(input_date):
    next_month = input_date + relativedelta(months=1)
    first_day_of_next_month = date(next_month.year, next_month.month, 1)
    return first_day_of_next_month - relativedelta(days=1)


def spending_money_savings_target_balance(
    pay_day, weekly_spending_amount, calculation_date=None, debug=False
):
    """Normalisies a monthly saving to cover spending money in a given cycle.
    Returns a target balance given a specific date (calculation_date).

    Note: A spending money cycle starts on the first day of the month
    following a 5 pay day month and ends on the last day of a 5 pay day month.
    """
    if calculation_date is None:
        calculation_date = date.today()

    one_day = relativedelta(days=1)
    one_month = relativedelta(months=1)
    first_date_of_cycle = None
    last_date_of_cycle = None

    # region Payments In
    # How many pay days are in the calculation month?
    calculation_month_pay_day_count = weekdays_in_range(
        pay_day,
        first_day_of_month(calculation_date),
        last_day_of_month(calculation_date),
    )

    if debug:
        print(
            f"Calculation Month Pay Day Count: {calculation_month_pay_day_count}"  # noqa
        )

    # How many times has a monthly saving been paid in since the last reset?
    payments_in = 0
    loop_date = calculation_date

    if calculation_month_pay_day_count == 5:
        # Count the current month.
        payments_in += 1
        # Roll back a month or the loop would never start.
        loop_date = loop_date - one_month

    while (
        weekdays_in_range(
            pay_day,
            first_day_of_month(loop_date),
            last_day_of_month(loop_date),
        )
        == 4
    ):
        payments_in += 1
        first_date_of_cycle = first_day_of_month(loop_date)
        loop_date = loop_date - one_month

    if debug:
        print(f"First Date of Cycle: {first_date_of_cycle}")
        print(f"Payments In: {payments_in}")

    # How many more times will a monthly saving be paid in?
    future_payements_in = 0

    if calculation_month_pay_day_count == 5:
        # There are no more payments in to come.
        last_date_of_cycle = last_day_of_month(calculation_date)
    else:
        loop_date = calculation_date + one_month
        previous_month_pay_day_count = 4
        while previous_month_pay_day_count == 4:
            future_payements_in += 1
            previous_month_pay_day_count = weekdays_in_range(
                pay_day,
                first_day_of_month(loop_date),
                last_day_of_month(loop_date),
            )
            last_date_of_cycle = last_day_of_month(loop_date)
            loop_date = loop_date + one_month

    if debug:
        print(f"Last Date of Cycle: {last_date_of_cycle}")
        print(f"Future Payments In: {future_payements_in}")

    # How many payments are there in the current cycle?
    total_payments_in = payments_in + future_payements_in
    # endregion

    # region Payments Out
    payments_out = weekdays_in_range(
        pay_day, first_date_of_cycle, calculation_date
    )

    if debug:
        print(f"Payments Out: {payments_out}")

    if calculation_date == last_date_of_cycle:
        future_payements_out = 0
    else:
        future_payements_out = weekdays_in_range(
            pay_day, calculation_date + one_day, last_date_of_cycle
        )

    if debug:
        print(f"Future Payments Out: {future_payements_out}")

    total_payments_out = payments_out + future_payements_out
    # endregion

    # region Montly Saving Calculation
    # How much should each payment in be?
    monthly_saving_amount = (
        weekly_spending_amount * total_payments_out
    ) / total_payments_in

    if debug:
        print(f"Monthly Saving Amount: £{monthly_saving_amount}")
    # endregion

    target_balance = (monthly_saving_amount * payments_in) - (
        weekly_spending_amount * payments_out
    )

    if debug:
        print(f"Target Balance: £{target_balance}")

    return target_balance


# spending_money_savings_target_balance(4, 65, calculation_date=date(2019, 1, 5), debug=True)  # noqa


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
