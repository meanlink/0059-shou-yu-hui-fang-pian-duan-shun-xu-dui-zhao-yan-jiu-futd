from fractions import Fraction
from itertools import combinations,product
from collections import defaultdict

def contrast(a,b):
    return Fraction(sum(b),len(b))-Fraction(sum(a),len(a))

def permute(rows):
    strata=defaultdict(lambda: {"A":[],"B":[]})
    for row in rows:
        strata[row["level"]][row["arm"]].append(row["score"])
    observed=Fraction(0)
    possible=[]
    labels=[]
    for label, arms in sorted(strata.items()):
        a,b=arms["A"],arms["B"]
        both=a+b
        weight=Fraction(len(both),len(rows))
        observed+=weight*contrast(a,b)
        sample=[]
        for pick in combinations(range(len(both)),len(a)):
            chosen=set(pick)
            test_a=[value for i,value in enumerate(both) if i in chosen]
            test_b=[value for i,value in enumerate(both) if i not in chosen]
            sample.append(weight*contrast(test_a,test_b))
        possible.append(sample)
        labels.append({"level":label,"a":len(a),"b":len(b),"effect":float(contrast(a,b))})
    extreme=0
    total=0
    for values in product(*possible):
        extreme+=abs(sum(values))>=abs(observed)
        total+=1
    return {"effect":float(observed),"p_value":extreme/total,"permutations":total,"detail":labels}
