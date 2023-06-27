from tinkoff.invest import Quotation

# specify the data type to correctly display attributes in IDE
def price_converter(price: Quotation):
    """Converts Quotation object to float"""

    num = '0' * (9-len(str(abs(price.nano)))) + str(abs(price.nano))
    return float(f'{abs(price.units)}.{num}')


def number_format(value):
    """Makes a good looking number."""

    return '{:,}'.format(value).replace(',', ' ')

def full_price_format(value):
    """Makes a good looking number."""

    new_value = round(value / 1000000, 2)
    if new_value < 0.01:
        new_value = number_format(value)
    else:
        new_value = f'{number_format(new_value)}M'

    return new_value