def normalize_phone_number(number):
    number = number.replace(" ", "")
    if number[:3] == '440':
        return number[2:]
    elif number[:2] == '44':
        return '0' + number[2:]
    elif number[:2] == '00':
        return number[1:]
    return number