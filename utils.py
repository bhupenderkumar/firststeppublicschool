
from functools import wraps
import bcrypt
from flask import redirect, request, session, url_for

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
def number_to_words(number):
    """
    Convert a number into words.
    :param number: The number to convert.
    :type number: int
    :return: The number in words.
    :rtype: str
    """
    number = int(float(number))
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    if number == 0:
        return 'Zero'
    elif number < 10:
        return ones[number]
    elif number < 20:
        return teens[number - 10]
    elif number < 100:
        return tens[number // 10] + ('' if number % 10 == 0 else ' ' + ones[number % 10])
    elif number < 1000:
        return ones[number // 100] + ' Hundred' + ('' if number % 100 == 0 else ' and ' + number_to_words(number % 100))
    elif number < 1000000:
        return number_to_words(number // 1000) + ' Thousand' + ('' if number % 1000 == 0 else ' ' + number_to_words(number % 1000))
    else:
        return 'Number out of range'
