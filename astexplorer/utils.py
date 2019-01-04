from datetime import date, time


class Sequence:

    def __init__(self):
        self.start_a = 0
        self.start_b = 0
        self.count = 1

    def __init__(self, a, b):
        self.start_a = a
        self.start_b = b
        self.count = 1

    def __str__(self):
        return '[' + str(self.start_a) + ' - ' + str(self.start_b) + ']' + ', ' + str(self.count)


def serialize(obj):
    if isinstance(obj, date):
        serial = obj.isoformat()
        return serial

    if isinstance(obj, time):
        serial = obj.isoformat()
        return serial

    return obj.__dict__


def find_sub_sequences(list_a, list_b, compare_f):
    seqs = []
    i = -1

    while i < len(list_a) - 1:
        i += 1
        j = -1
        while j < len(list_b) - 1:
            j += 1
            if not compare_f(list_a[i], list_b[j]):
                continue
            s = Sequence(i, j)
            seqs.append(s)
            k = i + 1
            j += 1
            while k < len(list_a) and j < len(list_b):
                if not compare_f(list_a[k], list_b[j]):
                    break
                s.count += 1
                j += 1
                k += 1
            i = k - 1
    return seqs
"""
for (var i = 0; i < listA.Length; i++)
{
    Sequence s = null;
    for (var j = 0; j < listB.Length; j++)
    {
        if (listA[i] != listB[j]) continue;
        s = new Sequence(i, j);
        seqs.Add(s);
        var k = i + 1;
        j++;
        while (k < listA.Length && j < listB.Length)
        {
            if (listA[k] != listB[j])
                break;            
            s.count++;
            j++;
            k++;
        }
        i = k - 1;
    }

"""

