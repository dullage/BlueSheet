#!/usr/bin/python3
from datetime import datetime
from dateutil.relativedelta import relativedelta


def calculations(
    weekly_spending_amount,
    pay_period_start_date,
    pay_period_end_date,
    pay_day,
    calculation_date=None
):
    """This old code needs refactoring but it works for now."""
    if calculation_date is None:
        calculation_date = datetime.today().date()

    # Calculate the beginning and end of the current pay period
    currentPayPeriodStart = calculation_date
    while currentPayPeriodStart.day != pay_period_start_date:
        currentPayPeriodStart = currentPayPeriodStart - relativedelta(days=1)

    currentPayPeriodEnd = calculation_date
    while currentPayPeriodEnd.day != pay_period_end_date:
        currentPayPeriodEnd = currentPayPeriodEnd + relativedelta(days=1)

    # Count the number of pay days between 2 dates
    def paydayCount(startDate, endDate):
        workingDate = startDate
        paydayCount = 0
        while workingDate <= endDate:
            if workingDate.weekday() == pay_day:
                paydayCount = paydayCount + 1
            workingDate = workingDate + relativedelta(days=1)
        return paydayCount

    # Count number of paydays before the end of the pay period
    remainingPayDayCount = paydayCount(calculation_date + relativedelta(days=1), currentPayPeriodEnd) # Add 1 day as we don't care if today is Friday (the money will have already been transfered)

    # Calculate the number of pay periods passed since (but excluding) the last 5 week pay period (including the current period)
    pastPeriods = 1 # The loop below starts on the previous period so start with a count of 1 to include the current period
    workingStartDate, workingEndDate, endReached = currentPayPeriodStart, currentPayPeriodEnd, False
    while endReached == False:    
        workingStartDate = workingStartDate - relativedelta(months=1)
        workingEndDate = workingEndDate - relativedelta(months=1)

        if paydayCount(workingStartDate, workingEndDate) == 5:
            endReached = True
        else:
            pastPeriods = pastPeriods + 1

    # Calculate the number of pay periods until (and including) the next 5 week pay period (excluding the current period)
    currentPeriodPaydayCount = paydayCount(currentPayPeriodStart, currentPayPeriodEnd)
    futurePeriods = 0
    if currentPeriodPaydayCount != 5: # If the current period has 5 weeks we're already at the end so the count can be left as 0
        workingStartDate, workingEndDate, endReached = currentPayPeriodStart, currentPayPeriodEnd, False
        while endReached == False:
            workingStartDate = workingStartDate + relativedelta(months=1)
            workingEndDate = workingEndDate + relativedelta(months=1)

            if paydayCount(workingStartDate, workingEndDate) == 5:
                futurePeriods = futurePeriods + 1 # Include the 5 week pay period in the future count
                endReached = True
            else:
                futurePeriods = futurePeriods + 1

    # Calculate the current goal target
    if futurePeriods > 0:
        goalTarget = (weekly_spending_amount * remainingPayDayCount)\
                    + ((weekly_spending_amount / (pastPeriods + futurePeriods)) * pastPeriods)
    else:
        goalTarget = (weekly_spending_amount * remainingPayDayCount) 

    # Return the result
    return {
        'current_month_start_date': currentPayPeriodStart,
        'current_month_end_date': currentPayPeriodEnd,
        'remaining_pay_day_count': remainingPayDayCount,
        'past_period_count': pastPeriods,
        'future_period_count': futurePeriods,
        'goal_target': goalTarget
    }
