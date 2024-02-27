import random


f = open("randomNumbers.txt", "w")

s = ""
for i in range(10000):
    s += str(random.randint(0, 3))
f.write(s)
f.close()

print(s.count("0"))
print(s.count("1"))
print(s.count("2"))
print(s.count("3"))