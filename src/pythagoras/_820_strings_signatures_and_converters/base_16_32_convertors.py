
base32_alphabet = '0123456789abcdefghijklmnopqrstuv'
base32_alphabet_map = {char:index for index,char in enumerate(base32_alphabet)}


def convert_base16_to_base32(hexdigest: str) -> str:
    """
    Convert a hexadecimal (base 16) string to a base 32 string.

    :name hexdigest: A string representing a hexadecimal number.
    :return: A string representing the equivalent number in base 32.
    """

    if not hexdigest:
        return '0'
    num = int(hexdigest,16)
    base32_str = convert_int_to_base32(num)

    return base32_str


def convert_int_to_base32(n: int) -> str:
    """
    Convert an integer to a base 32 string.

    :name n: An integer.
    :return: A string representing the equivalent number in base 32.
    """
    base32_str = ''
    while n > 0:
        base32_str = base32_alphabet[n & 31] + base32_str
        n >>= 5

    return base32_str

def convert_base_32_to_int(digest: str) -> int:
    """
    Convert a base 32 string to an integer.

    :name digest: A string representing a number in base 32.
    :return: An integer representing the equivalent number.
    """
    digest = digest.lower()
    num = 0
    for char in digest:
        num = num * 32 + base32_alphabet_map[char]
    return num

