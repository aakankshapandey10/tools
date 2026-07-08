from calculator import calculate

print(calculate("2 + 2 * 3"))
print(calculate("10 / 3"))
print(calculate("2 ** 10"))
print(calculate("2 + "))  # should return an error string, not crash
