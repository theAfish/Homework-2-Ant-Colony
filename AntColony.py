from handy_shader_functions import *

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
        self.ants_radius = 0.001
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

    @ti.kernel
    def set_puzzle(self):
        for i in range(-10, 10):
            for j in range(self.obstacle.size):
                self.obstacle.density_map[i, j] = 1
                self.obstacle.density_map[j, i] = 1
            unit = int(self.obstacle.size/5)
            for j in range(unit, 5*unit):
                self.obstacle.density_map[i+4*unit, j] = 1
            for j in range(unit, 4*unit):
                self.obstacle.density_map[i + unit, j] = 1
                self.obstacle.density_map[j, i+4*unit] = 1
            for j in range(unit, 2*unit):
                self.obstacle.density_map[j, i+unit] = 1
                self.obstacle.density_map[j+ 2*unit, i + unit] = 1
                self.obstacle.density_map[j + unit, i + 2*unit] = 1
                self.obstacle.density_map[j + unit, i + 3*unit] = 1
                self.obstacle.density_map[i + 3*unit, j+2*unit] = 1
                self.obstacle.density_map[i + 3 * unit, j + unit] = 1

    def draw_image(self):
        self.set_obstacle()
        self.set_food()
        if self.renderer.show_pheromone:
            self.set_pheromone()
        self.canvas.set_image(self.image)

    def draw_slime(self):
        self.set_pheromone()
        self.canvas.set_image(self.image/10.0)

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
                if self.window.is_pressed(ti.ui.SPACE):
                    self.is_paused[None] = 0
                if self.window.is_pressed("h") and self.window.is_pressed(ti.ui.LMB):
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
                    if i % 30 == 0:
                        self.ants.release_pheromone(self.size)
                    self.p_from_home.decay()
                    self.p_from_food.decay()
                self.draw_image()
                self.draw_home()
                if self.renderer.show_ants:
                    self.draw_ants()

                self.window.GUI.begin(self.renderer.name, 0.05, 0.05, 0.3, 0.4)
                if self.window.GUI.button("Restart"):
                    self.init()
                if self.window.GUI.button("Start"):
                    self.is_paused[None] = 0
                if self.window.GUI.button("Puzzle?"):
                    self.set_puzzle()
                self.window.GUI.text("Food Brush Size:")
                self.foods.brush_size[None] = self.window.GUI.slider_float(" ", self.foods.brush_size[None], 1, 40)
                self.window.GUI.text("Obstacle Brush Size:")
                self.obstacle.brush_size[None] = self.window.GUI.slider_float("", self.obstacle.brush_size[None], 1, 40)
                self.renderer.show_ants = self.window.GUI.checkbox("Show ants?", self.renderer.show_ants)
                self.renderer.show_pheromone = self.window.GUI.checkbox("Show pheromone?", self.renderer.show_pheromone)
                self.window.GUI.end()
                self.window.show()

    def slime_run(self):
        self.is_paused[None] = 1
        self.ants.slime_init()
        self.p_from_food.init()
        self.p_from_home.init()
        for i in range(10000000):
            if self.window.running:
                if self.window.is_pressed(ti.ui.SPACE):
                    self.is_paused[None] = 0
                if self.is_paused[None] == 0:
                    self.ants.slime_move()
                    if i % 1 == 0:
                        self.ants.slime_release_p(self.size)
                    self.p_from_home.decay()
                    self.p_from_food.decay()
                    # self.p_from_food.blur()
                    # self.p_from_home.blur()
                self.draw_image()
                # self.draw_ants()
                self.window.GUI.begin("Slime!", 0.05, 0.05, 0.3, 0.3)
                self.ants.detect_r[None] = self.window.GUI.slider_float("det_r", self.ants.detect_r[None], 1, 40)
                self.ants.detect_a[None] = self.window.GUI.slider_float("det_a", self.ants.detect_a[None], 0.0, pi)
                self.ants.sens[None] = self.window.GUI.slider_float("sens", self.ants.sens[None], -10.0, 10.0)
                self.ants.omgm[None] = self.window.GUI.slider_float("omgm", self.ants.omgm[None], 0.0, 1.0)
                self.p_from_food.decay_rate[None] = self.window.GUI.slider_float("dec_r_1", self.p_from_food.decay_rate[None], 0.0, 20.0*1e-3)
                self.p_from_home.decay_rate[None] = self.window.GUI.slider_float("dec_r_2", self.p_from_home.decay_rate[None], 0.0, 20.0*1e-3)

                self.window.GUI.end()
                self.window.show()


@ti.data_oriented
class Renderer:
    def __init__(self, size, resolution, name="Ant Colony"):
        self.name = name
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
    def __init__(self, N, speed, p_from_food, p_from_home, sensitivity, clock_delta, dt=1e-3, omgmax=pi*0.05):
        self.N = N
        self.speed = speed * dt
        self.detect_radius = 14
        self.detect_angle = 1.0 * pi/3
        self.sensitivity = sensitivity
        self.from_food = p_from_food
        self.from_home = p_from_home
        self.dt = dt
        self.omgmax = omgmax
        self.clock_max = 1.0
        self.clock_delta = dt * clock_delta
        self.pos = ti.Vector.field(2, dtype=ti.f32, shape=N)
        self.internal_clock = ti.field(dtype=ti.f32, shape=N)
        self.theta = ti.field(dtype=ti.f32, shape=N)
        self.attraction = ti.field(dtype=ti.f32, shape=N)
        self.is_home = ti.field(dtype=ti.i32, shape=N)

        self.detect_r = ti.field(dtype=ti.f32, shape=())
        self.sens = ti.field(dtype=ti.f32, shape=())
        self.omgm = ti.field(dtype=ti.f32, shape=())
        self.detect_a = ti.field(dtype=ti.f32, shape=())

    @ti.kernel
    def set_uniform_pos(self, pos: ti.template()):
        for i in self.pos:
            self.pos[i] = pos

    @ti.kernel
    def set_random_circle(self, pos: ti.template(), radius: ti.f32):
        for i in self.pos:
            self.pos[i] = pos + randUnit2D() * radius

    @ti.kernel
    def set_random_disk(self, pos: ti.template(), radius: ti.f32):
        for i in self.pos:
            self.pos[i] = pos + randUnit2D() * rand() * radius

    @ti.kernel
    def set_random_theta(self):
        for i in self.theta:
            self.theta[i] = rand() * 2.0 * pi

    @ti.kernel
    def init_clock(self):
        for i in self.internal_clock:
            self.internal_clock[i] = self.clock_max

    def default_init(self):
        self.num_init()
        self.set_random_circle(ti.Vector([0.5, 0.5]), 0.02)
        self.set_random_theta()
        self.init_clock()

    def num_init(self):
        self.sens[None] = self.sensitivity
        self.omgm[None] = self.omgmax
        self.detect_r[None] = self.detect_radius
        self.detect_a[None] = self.detect_angle

    def slime_init(self):
        self.num_init()
        self.set_random_disk(ti.Vector([0.5, 0.5]), 0.2)
        self.set_random_theta()
        self.set_half_home()

    @ti.kernel
    def set_half_home(self):
        for i in range(self.N/2):
            self.is_home[i] = 1

    @ti.kernel
    def random_ori(self):
        for i in self.theta:
            self.theta[i] += (rand() - 0.5) * 2.0 * self.omgm[None] + self.attraction[i]

    @ti.func
    def detect_things(self, idx, things, is_obstacle=False):
        center_index = ti.cast(self.pos[idx] * things.size, ti.i32)
        ds = ti.Vector([0.0, 0.0, 0.0], ti.f32)
        ns = ti.Vector([0, 0, 0], ti.i32)
        for i in range(-self.detect_r[None], self.detect_r[None]):
            for j in range(-self.detect_r[None], self.detect_r[None]):
                vec = ti.Vector([i, j], ti.i32)
                c_vec = vec + center_index
                d_angle = self.get_angle_diff(self.get_angle(vec), self.theta[idx])
                if self.detect_a[None]/3 < d_angle <= self.detect_a[None]/2:
                    ds[0] += things.density_map[c_vec]
                    ns[0] += 1
                elif self.detect_a[None]/3 < 2 * pi - d_angle <= self.detect_a[None]/2:
                    ds[2] += things.density_map[c_vec]
                    ns[2] += 1
                elif 0 < d_angle <= self.detect_a[None]/6 or 0 <= 2 * pi - d_angle < self.detect_a[None]/6:
                    ds[1] += things.density_map[c_vec]
                    ns[1] += 1
        for s in ti.static(range(3)):
            if ns[s] != 0:
                ds[s] /= ns[s]
        if ds[0] > max(ds[1], ds[2]):
            if is_obstacle:
                self.attraction[idx] = -0.3 #* ds[0]
            else:
                self.attraction[idx] += min(self.sens[None] * (ds[0]-ds[2]), self.detect_a[None] / 2)
        elif ds[2] > max(ds[1], ds[0]):
            if is_obstacle:
                self.attraction[idx] = 0.3 #* ds[2]
            else:
                self.attraction[idx] += -min(self.sens[None] * (ds[2]-ds[0]), self.detect_a[None] / 2)
        else:
            if is_obstacle and ds[1] > 0:
                self.theta[idx] -= pi/2 - rand() * pi
            else:
                self.attraction[idx] += 0.0

    @ti.func
    def nearest_angle(self, idx, things):
        center_index = ti.cast(self.pos[idx] * things.size, ti.i32)
        angle = self.theta[idx]
        nearest_pos = ti.Vector([100, 100], ti.i32)
        for i in range(-self.detect_r[None], self.detect_r[None]):
            for j in range(-self.detect_r[None], self.detect_r[None]):
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
            if (home_pos[0] - self.pos[i]).norm() <= home_radius:
                self.internal_clock[i] = self.clock_max
                if self.is_home[i] == 1:
                    self.is_home[i] = 0
                    self.theta[i] += pi
            elif (home_pos[0] - self.pos[i]).norm() <= home_radius + self.detect_r[None]/size and self.is_home[i] == 1:
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
                    self.internal_clock[i] = self.clock_max
                else:
                    self.theta[i] = self.nearest_angle(i, food)
            self.detect_things(i, obstacle, True)

    @ti.kernel
    def release_pheromone(self, size: ti.i32):
        for i in self.pos:
            int_pos = ti.cast(self.pos[i] * size, dtype=ti.i32)
            if self.is_home[i] == 1 and self.from_food.density_map[int_pos] < self.from_food.max_value:
                self.from_food.density_map[int_pos] = self.from_food.single_value * self.internal_clock[i]
                # self.from_food.set_area(int_pos, 1, self.internal_clock[i])
            elif self.is_home[i] == 0 and self.from_home.density_map[int_pos] < self.from_home.max_value:
                self.from_home.density_map[int_pos] = self.from_home.single_value * self.internal_clock[i]
                # self.from_home.set_area(int_pos, 1, self.internal_clock[i])
            if self.internal_clock[i] > 0.0:
                self.internal_clock[i] -= self.clock_delta

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
        int_pos = ti.cast(self.pos[idx]*self.from_food.size, ti.i32)
        self.from_food.wash_area(int_pos, 2)
        self.from_home.wash_area(int_pos, 2)
        self.pos[idx] -= ti.Vector([ti.cos(self.theta[idx]), ti.sin(self.theta[idx])]) * self.speed
        int_new_pos = ti.cast(self.pos[idx]*self.from_food.size, ti.i32)
        self.from_food.wash_area(int_new_pos, 2)
        self.from_home.wash_area(int_new_pos, 2)
        self.theta[idx] -= pi/2 - rand() * pi

    def move(self, home_pos, home_r, food, size, obstacle):
        self.detect(home_pos, home_r, food, obstacle, size)
        self.random_ori()
        self.update_pos(obstacle)
        self.pbc()

    @ti.kernel
    def slime_detect(self):
        for i in range(self.N):
            self.attraction[i] = 0.0
            if self.is_home[i] == 1:
                self.detect_things(i, self.from_home)
            else:
                self.detect_things(i, self.from_food)

    @ti.kernel
    def slime_update(self):
        for i in self.pos:
            self.pos[i] += ti.Vector([ti.cos(self.theta[i]), ti.sin(self.theta[i])]) * self.speed
            for d in ti.static(range(2)):
                if self.pos[i][d] < 0:  # Bottom and left
                    self.pos[i][d] = 0  # move particle inside
                    self.theta[i] *= -1  # stop it from moving further

                if self.pos[i][d] > 1:  # Top and right
                    self.pos[i][d] = 1  # move particle inside
                    self.theta[i] *= -1  # stop it from moving further


    @ti.kernel
    def slime_release_p(self, size: ti.i32):
        for i in self.pos:
            int_pos = ti.cast(self.pos[i] * size, dtype=ti.i32)
            if self.is_home[i] == 1 and self.from_food.density_map[int_pos] < self.from_food.max_value:
                self.from_food.density_map[int_pos] = self.from_food.single_value
            elif self.is_home[i] == 0 and self.from_home.density_map[int_pos] < self.from_home.max_value:
                self.from_home.density_map[int_pos] = self.from_home.single_value

    def slime_move(self):
        self.slime_detect()
        self.random_ori()
        self.slime_update()
        # self.pbc()

    def get_ants(self):
        return self.pos


@ti.data_oriented
class Detectables:
    def __init__(self, canvas, decay_rate, single_value, max_value, brush_size=None):
        self.init_decay_rate = decay_rate
        self.max_value = max_value
        self.single_value = single_value
        self.canvas = canvas
        self.size = self.canvas.size
        self.density_map = ti.field(dtype=ti.f32, shape=(canvas.size, canvas.size))
        self.init_brush_size = brush_size
        self.brush_size = ti.field(dtype=ti.f32, shape=())
        self.decay_rate = ti.field(dtype=ti.f32, shape=())

    def init_brush(self):
        self.brush_size[None] = self.init_brush_size

    @ti.func
    def minus(self, pos):
        if self.density_map[pos] > 0:
            self.density_map[pos] -= 1

    @ti.kernel
    def init(self):
        self.decay_rate[None] = self.init_decay_rate
        for i, j in self.density_map:
            self.density_map[i, j] = 0.0

    @ti.kernel
    def decay(self):
        for i, j in self.density_map:
            if self.density_map[i, j] > 0:
                self.density_map[i, j] -= self.decay_rate[None]
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

    @ti.func
    def set_area(self, center, radius, rate):
        for i in range(center[0]-radius, center[0]+radius):
            for j in range(center[1]-radius, center[1]+radius):
                self.density_map[i, j] += self.single_value * rate

    @ti.func
    def wash_area(self, center, radius):
        for i in range(center[0]-radius, center[0]+radius):
            for j in range(center[1]-radius, center[1]+radius):
                self.density_map[i, j] = 0.0

    @ti.kernel
    def blur(self):
        for i, j in self.density_map:
            self.density_map[i, j] = (self.density_map[i-1, j] + self.density_map[i+1, j] + self.density_map[i, j+1] + self.density_map[i, j-1]+ self.density_map[i, j])/ 5


