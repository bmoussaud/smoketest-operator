
from datetime import date
b_date = date(2021, 1, 28)
f_date = date(2021, 3, 1)
l_date = date(2022, 1, 28)
delta = l_date - f_date
delta2 = l_date - b_date
print(delta.days)
print(delta2.days)

ratio = (delta.days/delta2.days)
print(ratio)
