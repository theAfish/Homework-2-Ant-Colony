from AntColony import *

ti.init(arch=ti.gpu)
dt = 1e-3

rdr = Renderer(512, 512)

ph = Detectables(rdr, 0.2*dt, 1.0, 1.0)
pf = Detectables(rdr, 0.2*dt, 2.0, 2.0)
ants = Ants(2000, 1.0, pf, ph, 1.5, 10.0)
ac = AntColony(rdr, ants, ph, pf)

if __name__ == "__main__":
    ac.run()
