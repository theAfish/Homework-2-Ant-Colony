from taichi_glsl import *

@ti.data_oriented
class AntColony:
    def __init__(self, renderer=None, ants=None, p_from_home=None, p_from_food=None):
        self.renderer = renderer
        self.size = renderer.size
        self.ants = ants
        self.p_from_home = p_from_home
        self.ph_color = ti.Vector([0.8, 0.8, 0.0])
        self.p_from_food = p_from_food
        self.pf_color = ti.Vector([0.0, 0.5, 0.9])
        self.obstacle = Detectables(self.renderer, 0, 1, 1, 10)
        self.foods = Detectables(self.renderer, 0, 2, 2, 20)
        self.home_pos = ti.Vector.field(2, dtype=float, shape=(1, ))
        self.home_radius = 0.02
        self.ants_radius = 0.002
        self.is_paused = ti.field(dtype=ti.i32, shape=[])
        self.window = renderer.window
        self.canvas = self.window.get_canvas()
        self.image = ti.Vector.field(3, dtype=ti.f32, shape=(self.size, self.size))

    def set_ants(self, ants):
        self.ants = ants

    def create_new_ants(self, N, speed, dt=1e-3):
        self.ants = Ants(N, speed, dt)

    def draw_canvas(self):
        self.canvas.set_image(self.renderer.get_image())

    @ti.kernel
    def set_pheromone(self):
        for i, j in self.image:
            self.image[i, j] += self.p_from_home.density_map[i, j] * self.ph_color + self.p_from_food.density_map[i, j] * self.pf_color

    @ti.kernel
    def set_food(self):
        for i, j in self.image:
            if self.foods.density_map[i, j] > 0:
                self.image[i, j] = (0.7, 0.8, 0.2)

    @ti.kernel
    def set_obstacle(self):
        for i, j in self.image:
            if self.obstacle.density_map[i, j] == 1:
                self.image[i, j] = (0.4, 0.4, 0.4)
            else:
                self.image[i, j] = (0.0, 0.0, 0.0)

    def draw_image(self):
        self.set_obstacle()
        self.set_food()
        if self.renderer.show_pheromone:
            self.set_pheromone()
        self.canvas.set_image(self.image)

    def draw_ants(self):
        self.canvas.circles(self.ants.get_ants(), self.ants_radius, (0.9, 0.9, 0.9))

    def draw_home(self):
        self.canvas.circles(self.home_pos, self.home_radius, (0.5, 0.5, 1.0))

    def init(self):
        self.is_paused[None] = 1
        self.foods.init()
        self.ants.default_init()
        self.p_from_food.init()
        self.p_from_home.init()
        self.obstacle.init()

    def run(self):
        self.is_paused[None] = 1
        self.ants.default_init()
        self.foods.init_brush()
        self.obstacle.init_brush()
        self.home_pos[0] = [0.5, 0.5]
        for i in range(1000000):
            if self.window.running:
                mouse = self.window.get_cursor_pos()
                for e in self.window.get_events(ti.ui.PRESS):
                    if e.key in [ti.ui.SPACE]:
                        self.is_paused[None] = 0
                    elif self.window.is_pressed("h") and e.key == ti.ui.LMB:
                        self.home_pos[0] = ti.Vector([mouse[0], mouse[1]])
                        self.ants.set_random_circle(ti.Vector([mouse[0], mouse[1]]), self.home_radius)
                if self.window.is_pressed("f"):
                    if self.window.is_pressed(ti.ui.LMB):
                        self.foods.draw(ti.Vector([mouse[0], mouse[1]]), 2)
                    elif self.window.is_pressed(ti.ui.RMB):
                        self.foods.draw(ti.Vector([mouse[0], mouse[1]]), 0)
                elif self.window.is_pressed("d"):
                    if self.window.is_pressed(ti.ui.LMB):
                        self.obstacle.draw(ti.Vector([mouse[0], mouse[1]]), 1)
                    elif self.window.is_pressed(ti.ui.RMB):
                        self.obstacle.draw(ti.Vector([mouse[0], mouse[1]]), 0)

                if self.is_paused[None] == 0:

                    self.ants.move(self.home_pos, self.home_radius, self.foods, self.size, self.obstacle)
                    if i % 40 == 0:
                        self.ants.release_pheromone(self.size)
                    self.p_from_home.decay()
                    self.p_from_food.decay()
                self.draw_image()
                self.draw_home()
                if self.renderer.show_ants:
                    self.draw_ants()

                self.window.GUI.begin(self.renderer.name, 0.05, 0.05, 0.3, 0.4)
                if self.window.GUI.button("restart"):
                    self.init()
                if self.window.GUI.button("start"):
                    self.is_paused[None] = 0
                self.window.GUI.text("Food Brush Size:")
                self.foods.brush_size[None] = self.window.GUI.slider_float(" ", self.foods.brush_size[None], 1, 40)
                self.window.GUI.text("Obstacle Brush Size:")
                self.obstacle.brush_size[None] = self.window.GUI.slider_float("", self.obstacle.brush_size[None], 1, 40)
                self.renderer.show_ants = self.window.GUI.checkbox("Show ants?", self.renderer.show_ants)
                self.renderer.show_pheromone = self.window.GUI.checkbox("Show pheromone?", self.renderer.show_pheromone)
                self.window.GUI.end()
                self.window.show()

@ti.data_oriented
class Renderer:
    def __init__(self, size, resolution):
        self.name = "Ant Colony"
        self.size = size
        self.res = resolution
        self.bg_color = [0, 0, 0]
        self.canvas = ti.Vector.field(3, dtype=ti.f32, shape=(size, size))
        self.window = ti.ui.Window(self.name, (self.res, self.res))
        self.show_ants = True
        self.show_pheromone = True
        self.show_home = True

@ti.data_oriented
class Ants:
    def __init__(self, N, speed, p_from_food, p_from_home, sensitivity, dt=1e-3, omgmax=0.2):
        self.N = N
        self.speed = speed
        self.detect_radius = 30
        self.detect_angle = 1.5 * pi/3
        self.sensitivity = sensitivity
        self.from_food = p_from_food
        self.from_home = p_from_home
        self.dt = dt
        self.omgmax = omgmax
        self.pos = ti.Vector.field(2, dtype=ti.f32, shape=N)
        self.theta = ti.field(dtype=ti.f32, shape=N)
        self.attraction = ti.field(dtype=ti.f32, shape=N)
        self.is_home = ti.field(dtype=ti.i32, shape=N)

    @ti.kernel
    def set_uniform_pos(self, pos: ti.template()):
        for i in self.pos:
            self.pos[i] = pos

    @ti.kernel
    def set_random_circle(self, pos: ti.template(), radius: ti.f32):
        for i in self.pos:
            self.pos[i] = pos + randUnit2D() * radius

    @ti.kernel
    def set_random_theta(self):
        for i in self.theta:
            self.theta[i] = rand() * 2.0 * pi

    def default_init(self):
        self.set_random_circle(ti.Vector([0.5, 0.5]), 0.03)
        self.set_random_theta()

    @ti.kernel
    def random_ori(self):
        for i in self.theta:
            self.theta[i] += (rand() - 0.5) * 2.0 * self.omgmax + self.attraction[i]

    @ti.func
    def detect_things(self, idx, things, is_obstacle=False):
        center_index = ti.cast(self.pos[idx] * things.size, ti.i32)
        ds = ti.Vector([0.0, 0.0, 0.0], ti.f32)
        ns = ti.Vector([0, 0, 0], ti.i32)
        for i in range(-self.detect_radius, self.detect_radius):
            for j in range(-self.detect_radius, self.detect_radius):
                vec = ti.Vector([i, j], ti.i32)
                c_vec = vec + center_index
                d_angle = self.get_angle_diff(self.get_angle(vec), self.theta[idx])
                if self.detect_angle/3 < d_angle <= self.detect_angle/2:
                    ds[0] += things.density_map[c_vec]
                    ns[0] += 1
                elif self.detect_angle/3 < 2 * pi - d_angle <= self.detect_angle/2:
                    ds[2] += things.density_map[c_vec]
                    ns[2] += 1
                elif 0 < d_angle <= self.detect_angle/6 or 0 <= 2 * pi - d_angle < self.detect_angle/6:
                    ds[1] += things.density_map[c_vec]
                    ns[1] += 1
        for s in ti.static(range(3)):
            if ns[s] != 0:
                ds[s] /= ns[s]
        if ds[0] > max(ds[1], ds[2]):
            if is_obstacle:
                self.attraction[idx] = -0.1 * ds[0]
            else:
                self.attraction[idx] += min(self.sensitivity * ds[0], self.detect_angle / 2)
        elif ds[2] > max(ds[1], ds[0]):
            if is_obstacle:
                self.attraction[idx] = 0.1 * ds[2]
            else:
                self.attraction[idx] += -min(self.sensitivity * ds[2], self.detect_angle / 2)
        else:
            self.attraction[idx] += 0.0

    @ti.func
    def nearest_angle(self, idx, things):
        center_index = ti.cast(self.pos[idx] * things.size, ti.i32)
        angle = self.theta[idx]
        nearest_pos = ti.Vector([100, 100], ti.i32)
        for i in range(-self.detect_radius, self.detect_radius):
            for j in range(-self.detect_radius, self.detect_radius):
                vec = ti.Vector([i, j], ti.i32)
                c_vec = vec + center_index
                if things.density_map[c_vec] > 0:
                    if vec.norm() < nearest_pos.norm():
                        nearest_pos = vec
        if nearest_pos.norm() < 50.0:
            angle = self.get_angle(nearest_pos)
        return angle

    @ti.kernel
    def detect(self, home_pos: ti.template(), home_radius: ti.f32, food: ti.template(), obstacle: ti.template(), size:ti.f32):
        for i in range(self.N):
            self.attraction[i] = 0.0
            if (home_pos[0] - self.pos[i]).norm() <= home_radius and self.is_home[i] == 1:
                self.is_home[i] = 0
                self.theta[i] += pi
            elif (home_pos[0] - self.pos[i]).norm() <= home_radius + self.detect_radius/size and self.is_home[i] == 1:
                self.theta[i] = self.get_angle(home_pos[0] - self.pos[i])
            if self.is_home[i] == 1:
                self.detect_things(i, self.from_home)
            else:
                self.detect_things(i, self.from_food)
                c = ti.cast(self.pos[i] * food.size, ti.i32)
                if food.density_map[c] > 0:
                    food.minus(c)
                    self.is_home[i] = 1
                    self.theta[i] += pi
                else:
                    self.theta[i] = self.nearest_angle(i, food)
            self.detect_things(i, obstacle, True)

    @ti.kernel
    def release_pheromone(self, size: ti.i32):
        for i in self.pos:
            int_pos = ti.cast(self.pos[i] * size, dtype=ti.i32)
            if self.is_home[i] == 1 and self.from_food.density_map[int_pos] < self.from_food.max_value:
                self.from_food.density_map[int_pos] += self.from_food.single_value
            elif self.is_home[i] == 0 and self.from_home.density_map[int_pos] < self.from_home.max_value:
                self.from_home.density_map[int_pos] += self.from_home.single_value

    @ti.func
    def get_angle(self, vec):
        angle = acos(ti.Vector([1, 0]).dot(vec.normalized()))
        if vec[1] < 0:
            angle *= -1
        return angle

    @ti.func
    def get_angle_diff(self, angle1, angle2):
        return (angle1 - angle2) % (2 * pi)

    @ti.kernel
    def update_pos(self, obstacle: ti.template()):
        for i in self.pos:
            self.pos[i] += ti.Vector([ti.cos(self.theta[i]), ti.sin(self.theta[i])]) * self.speed
            if obstacle.density_map[ti.cast(self.pos[i] * obstacle.size, ti.i32)] != 0:
                self.move_back(i)
            if obstacle.density_map[ti.cast(self.pos[i] * obstacle.size, ti.i32)] != 0:
                self.pos[i] = [0,0]

    @ti.kernel
    def pbc(self):
        for i in self.pos:
            self.pos[i] -= ti.Vector([0.5, 0.5])
            for d in ti.static(range(2)):
                self.pos[i][d] -= round(self.pos[i][d])
            self.pos[i] += ti.Vector([0.5, 0.5])

    @ti.func
    def move_back(self, idx):
        self.pos[idx] -= ti.Vector([ti.cos(self.theta[idx]), ti.sin(self.theta[idx])]) * self.speed
        self.theta[idx] -= pi

    def move(self, home_pos, home_r, food, size, obstacle):
        self.detect(home_pos, home_r, food, obstacle, size)
        self.random_ori()
        self.update_pos(obstacle)
        self.pbc()

    def get_ants(self):
        return self.pos


@ti.data_oriented
class Detectables:
    def __init__(self, canvas, decay_rate, single_value, max_value, brush_size=None):
        self.decay_rate = decay_rate
        self.max_value = max_value
        self.single_value = single_value
        self.canvas = canvas
        self.size = self.canvas.size
        self.density_map = ti.field(dtype=ti.f32, shape=(canvas.size, canvas.size))
        self.init_brush_size = brush_size
        self.brush_size = ti.field(dtype=ti.f32, shape=())

    def init_brush(self):
        self.brush_size[None] = self.init_brush_size

    @ti.func
    def minus(self, pos):
        if self.density_map[pos] > 0:
            self.density_map[pos] -= 1

    @ti.kernel
    def init(self):
        for i, j in self.density_map:
            self.density_map[i, j] = 0.0

    @ti.kernel
    def decay(self):
        for i, j in self.density_map:
            if self.density_map[i, j] > 0:
                self.density_map[i, j] -= self.decay_rate
            elif self.density_map[i, j] < 0:
                self.density_map[i, j] = 0

    @ti.kernel
    def draw(self, pos: ti.template(), value: ti.i32):
        center = ti.cast(pos * self.size, ti.i32)
        size = ti.cast(self.brush_size[None], ti.i32)
        for i in range(-size, size):
            for j in range(-size, size):
                if ti.Vector([i, j]).norm() <= self.brush_size[None]:
                    self.density_map[center + (i, j)] = value

    @ti.kernel
    def blur(self):
        for i, j in self.density_map:
            self.density_map[i, j] = (self.density_map[i-1, j] + self.density_map[i+1, j] + self.density_map[i, j+1] + self.density_map[i, j-1]+ self.density_map[i, j])/ 5
