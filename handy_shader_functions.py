import taichi as ti
from taichi import acos, round
import math
@ti.func
def randUnit2D():
    a = ti.random() * math.tau
    return ti.Vector([ti.cos(a), ti.sin(a)])

@ti.func
def rand():
    return ti.random()

pi = math.pi
