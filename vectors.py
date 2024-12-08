import math as maths
import numpy as np
x = 0
y = 1

## Finds the dot product of two vectors
def dot(vec1, vec2):
    if len(vec1) != len(vec2):
        print("Dimension error!")
        return
    return sum([vec1[i]*vec2[i] for i in range(len(vec1))])

## Finds the magnitude of a vector
def mag(vec):
    mag = sum([i**2 for i in vec])
    return maths.sqrt(mag)

## Returns a vector with the same direction as the input of length 1
def unit(vec):
    if mag(vec) == 0:
        return vec
    return vec*(1/mag(vec))

## Returns a direction vector (a vector of unit length 1 so it can easily be scaled) that is perpendicular to input line
## By taking the "negative reciprocal", swapping the values and multiplying one of them by -1
def normal(vec):
    normal = np.array([-1*vec[y],vec[x]])
    return unit(normal)

## Main is just used for testing purposes
def main():
    print("DOT PRODUCT BETWEEN (-1,-2), (3,4):", dot(np.array([1, 2]), np.array([3, 4])))
    print('---')
    print("MAGNITUDE OF (3,4):", mag(np.array([3, 4])))
    print("UNIT OF (3,4):", unit(np.array([3,4])))
    print("NORMAL TO (3, 4):", normal(np.array([3, 4])))
    print("DOT BETWEEN NORMAL TO (3,4) AND (3,4) SHOULD BE ZERO:", dot(np.array([3, 4]), normal(np.array([3, 4]))))
    print('---')
    print("MAGNITUDE OF (-1, -2):", mag(np.array([-1,- 2])))
    print("UNIT OF (-1, -2):", unit(np.array([-1,- 2])))
    print("NORMAL TO (-1, -2):", normal(np.array([-1,- 2])))
    print("DOT BETWEEN NORMAL TO (-1, -2) AND (-1, -2) SHOULD BE ZERO:", dot(np.array([-1, -2]), normal(np.array([-1,- 2]))))

if __name__ == "__main__":
    main()