from AntColony import *

ti.init(arch=ti.gpu)


rdr = Renderer(512, 512)

ph = Detectables(rdr, 0.0017, 2.0, 2.0)
pf = Detectables(rdr, 0.0017, 2.0, 2.0)
ants = Ants(1500, 0.0006, pf, ph, 0.25)
ac = AntColony(rdr, ants, ph, pf)

if __name__ == "__main__":
    ac.run()
