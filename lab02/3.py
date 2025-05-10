from scipy.special import comb

sum = 0

for n in range(12, 20+1):
    sum += (comb(60, n)) * (0.2 ** n) * (0.8 ** (60-n))

print(sum)