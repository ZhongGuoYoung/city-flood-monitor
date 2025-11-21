from typing import List

nums = [8, 1, 2, 2, 3]
n = len(nums)
arr = []
for i in range(0, n):
    a = 0
    for j in range(0, n):
        if nums[i] > nums[j]:
            a += 1

    arr.append(a)

return arr
