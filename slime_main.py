from AntColony import *

ti.init(arch=ti.gpu)
dt = 1e-3

rdr = Renderer(600, 600)

ph = Detectables(rdr, 5.0*dt, 1.0, 1.0)
pf = Detectables(rdr, 5.0*dt, 1.0, 1.0)
ants = Ants(50000, 1.0, pf, ph, 0.1, 10.0)
ac = AntColony(rdr, ants, ph, pf)

if __name__ == "__main__":
    ac.slime_run()
