def checkPalindrome(string):
    start = 0
    last = len(string) - 1
    
    string_list = list(string)
    print(string_list)
    
    
    while(last > start):
        x = string_list[start]
        y = string_list[last]
        string_list[last] = x
        string_list[start] = y
        start += 1
        last -= 1

    return "".join(string_list) == string

string = input()
print("Palindrome: ", checkPalindrome(string))