

def factorial(i):
    order = [i]
    while i != 1:
        i = i - 1
        order.append(i)

    product = 1
    for num in order:
        product = num * product

    return product

print factorial(5)
