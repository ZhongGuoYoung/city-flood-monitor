citations = [0,0]
citations.sort(reverse=True)
print(len(citations))

for i in range(0, len(citations)):
    if i+1 > citations[i]:
        print(i)
        break
print(len(citations))

