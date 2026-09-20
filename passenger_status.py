def get_delay_status(arrival_delay):
    """
    Convert train delay into a passenger-friendly status.
    """

    if arrival_delay <= 0:
        return "ON TIME"

    elif arrival_delay <= 15:
        return "SLIGHTLY DELAYED"

    elif arrival_delay <= 60:
        return "DELAYED"

    else:
        return "HEAVILY DELAYED"