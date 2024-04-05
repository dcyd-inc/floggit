import string, random

def get_random_string(n=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))
