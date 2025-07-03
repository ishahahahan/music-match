def twoSum( nums, target):
    """
    :type nums: List[int]
    :type target: int
    :rtype: List[int]
    """
    num = {}
    for i in range(0, len(nums)):
        if((target - nums[i])in num):
            return [num[target-nums[i]], i]
        else:
            num[nums[i]] = i

    return []

print(twoSum([2, 7, 11, 15], 9))  