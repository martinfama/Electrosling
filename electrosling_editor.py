import pygame
import math
from pygame import gfxdraw
pygame.init()

size = [1600, 900]
screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
scale = 1.0
mouse_pos_old = [0, 0]
font = pygame.font.Font("AvenirLTPro-Black.otf", 20)
levels_file = open("levels_2.txt")

object_count = 0
objects = []
lines = []

my_dot_vel = [0.0, 0.0]
my_dot_pos = [-450.0, 0.0]
my_dot_color = [255, 0, 255]
my_dot_mass = 216.0

objective = [500.0, 0.0]
objective_size = 10000.0

reset = False

class attractor:
    def __init__(self):
        self.pos = [0.0, 0.0]
        self.sign = 1
        self.charge = 0.0
        self.kind = "" #"dot", "box"
        self.length = 0.0
        self.alpha = 0.0 #angle
        self.sin_a = 0.0
        self.cos_a = 0.0
        self.color = [255, 0, 0]

    def modify(self, mouse_pos, button, num, keys):
        global selected
        pixel_pos = coor_to_pixel(self.pos)
        if self.kind == "dot":
            if (pixel_pos[0]-mouse_pos[0])**2+(pixel_pos[1]-mouse_pos[1])**2 < 100.0:
                if button == 1:
                    selected = num
                if button == 2:
                    self.sign *= -1
                    if self.sign == 1:
                        self.color = [255, 0, 0]
                    else:
                        self.color = [0, 0, 255]
                if button == 3:
                    return True
                if button == 4:
                    sim_add = 10**math.floor(math.log10(self.charge)+1.0)/10.0
                    self.charge += sim_add
                if button == 5:
                    sim_add = 10**math.floor(math.log10(self.charge)+1.0)/10.0
                    if self.charge == sim_add:
                        self.charge -= sim_add/10.0
                    else:
                        self.charge -= sim_add
        elif self.kind == "box":
            if (pixel_pos[0]-mouse_pos[0])**2+(pixel_pos[1]-mouse_pos[1])**2 < 100.0:
                if button == 1:
                    selected = num
                if button == 2:
                    self.sign *= -1
                    if self.sign == 1:
                        self.color = [255, 0, 0]
                    else:
                        self.color = [0, 0, 255]
                if button == 3:
                    return True
                if button == 4:
                    if keys[pygame.K_TAB]:
                        self.charge += 100.0
                    elif keys[pygame.K_z]:
                        self.alpha += math.pi/16.0
                        self.cos_a = math.cos(self.alpha)
                        self.sin_a = math.sin(self.alpha)
                    else:
                        self.length += 10
                if button == 5:
                    if keys[pygame.K_TAB]:
                        self.charge -= 100.0
                        self.charge = max(100.0, self.charge)
                    elif keys[pygame.K_z]:
                        self.alpha -= math.pi/16.0
                        self.cos_a = math.cos(self.alpha)
                        self.sin_a = math.sin(self.alpha)
                    else:
                        self.length -= 10
                        self.length = max(10.0, self.length)

    def act_upon(self, d_time, local_vel, local_pos):
        global reset
        if self.kind == "dot":
            if (self.pos[0]-local_pos[0])**2+(self.pos[1]-local_pos[1])**2 < ((self.charge)**(1.0/3.0)+(my_dot_mass)**(1.0/3.0))**2:
                return False
            d_y = self.pos[1]-local_pos[1]
            d_x = self.pos[0]-local_pos[0]
            r = math.sqrt(d_x**2+d_y**2)
            s_a = d_y/1.0/r
            c_a = d_x/1.0/r
            acceleration = acceleration_const/(d_y**2+d_x**2)*self.charge*self.sign
            if local_vel == False or local_vel == None:
                return False
            local_vel[0] += acceleration*c_a/1.0/r*d_time
            local_vel[1] += acceleration*s_a/1.0/r*d_time
        elif self.kind == "box":
            t_x = local_pos[0]-self.pos[0]
            t_y = local_pos[1]-self.pos[1]
            r_x = t_x*self.cos_a + t_y*self.sin_a + self.pos[0]
            r_y = -t_x*self.sin_a + t_y*self.cos_a + self.pos[1]
            d_theta = self.pos[0] + self.length - r_x
            d_beta = r_x - self.pos[0]
            d_r = r_y-self.pos[1]
            f = [self.pos[0]-r_x, self.pos[1]-r_y]
            a = self.length**2
            b = 2*f[0]*self.length
            c = f[0]**2+f[1]**2-my_dot_mass**(2.0/3.0)
            discriminant = b**2-4*a*c
            if discriminant >= 0.0:
                discriminant = math.sqrt(discriminant)
                t1 = (-b - discriminant)/(2*a)
                t2 = (-b + discriminant)/(2*a)
                if (t1 >= 0 and t1 <= 1) or (t2 >= 0 and t2 <= 1):
                    return False
            #pygame.draw.circle(screen, self.color, coor_to_pixel([r_x, r_y]), 3)
            #pygame.draw.circle(screen, self.color, coor_to_pixel(self.pos), 10)
            #pygame.draw.line(screen, self.color, coor_to_pixel(self.pos), coor_to_pixel([self.pos[0]+self.length, self.pos[1]]))
            if d_r != 0.0:
                sin_theta = d_theta/math.sqrt(d_r**2+d_theta**2)
                sin_beta = d_beta/math.sqrt(d_r**2+d_beta**2)
                cos_theta = d_r/math.sqrt(d_r**2+d_theta**2)
                cos_beta = d_r/math.sqrt(d_r**2+d_beta**2)
                F_r_x = self.charge/4.0/math.pi/d_r*(cos_beta-cos_theta)*self.sign
                F_r_y = self.charge/4.0/math.pi/d_r*(sin_beta+sin_theta)*self.sign*(-1)
            else:
                a = self.pos[0]-r_x
                b = a+self.length
                F_r_x = self.charge/4.0/math.pi/a*self.sign - self.charge/4.0/math.pi/b*self.sign
                if r_x > self.pos[0]:
                    F_r_x *= -1
                F_r_y = 0.0
            F_x = -F_r_y*self.sin_a + F_r_x*self.cos_a
            F_y = F_r_y*self.cos_a + F_r_x*self.sin_a
            if local_vel == False or local_vel == None:
                return False
            local_vel[0] += F_x*d_time
            local_vel[1] += F_y*d_time
        return [local_vel[0], local_vel[1]]

    def draw(self):
        if self.kind == "dot":
            pixel_points = coor_to_pixel(self.pos)
            radius = int((self.charge)**(1.0/3.0)*scale)
            gfxdraw.filled_circle(screen, pixel_points[0], pixel_points[1], radius, self.color)
            if radius > 1:
                gfxdraw.aacircle(screen, pixel_points[0], pixel_points[1], radius, self.color)
        elif self.kind == "box":
            pixel_pos = coor_to_pixel(self.pos, True)
            end_pos = [self.pos[0]+self.length*self.cos_a, self.pos[1]+self.length*self.sin_a]
            pixel_end_pos = coor_to_pixel(end_pos)
            #pygame.draw.aaline(screen, self.color, (pixel_pos[0], pixel_pos[1]), coor_to_pixel([self.pos[0]+self.length*self.cos_a, self.pos[1]+self.length*self.sin_a], True))
            pygame.draw.line(screen, self.color, (pixel_pos[0], pixel_pos[1]), coor_to_pixel([self.pos[0]+self.length*self.cos_a, self.pos[1]+self.length*self.sin_a]), int(self.charge**(1.0/3.0)/scale/2.0)+1)
            #pygame.draw.line(screen, self.color, (int(pixel_pos[0]), int(pixel_pos[1])), ())
            gfxdraw.aacircle(screen, int(pixel_pos[0]), int(pixel_pos[1]), 10, self.color)

    def show_info(self):
        label = font.render("x: " + str(self.pos[0]), 1, (0, 0, 0))
        screen.blit(label, [10, 10])
        label = font.render("y: " + str(self.pos[1]), 1, (0, 0, 0))
        screen.blit(label, [10, label.get_rect()[3]+10])
        label = font.render("Charge: " + str(self.charge), 1, (0, 0, 0))
        screen.blit(label, [10, label.get_rect()[3]*2+10])

def coor_to_pixel(coors = [0.0, 0.0], f_or_i = False):
    global scale
    if not f_or_i:
        return [int(coors[0]*scale+size[0]/2), int(-coors[1]*scale+size[1]/2)]
    else:
        return [coors[0]*scale+size[0]/2.0, -coors[1]*scale+size[1]/2.0]
def pixel_to_coor(pixel = [0, 0]):
    global scale
    return [int((pixel[0]-size[0]/2)/scale), int(-(pixel[1]-size[1]/2)/scale)]

def simulate(l_secs = 0.0, steps = 0, vel = [0.0, 0.0], pos=[0.0, 0.0]):
    local_pos = [pos[0], pos[1]]
    local_vel = [vel[0], vel[1]]
    for x in range(steps):
        for i in range(object_count):
            local_vel = objects[i].act_upon(l_secs, local_vel, local_pos)
        if local_vel == False:
            break
        prev_dots = [local_pos[0], local_pos[1]]
        local_pos[0] += local_vel[0]*l_secs
        local_pos[1] += local_vel[1]*l_secs
        green = int(255.0/steps*x)
        blue = int(255.0/steps*x)
        pygame.draw.aaline(screen, (255, green, blue), coor_to_pixel(prev_dots, True), coor_to_pixel(local_pos, True), True)
        total_velocity = math.sqrt(local_vel[0]**2 + local_vel[1]**2)
        try:
            l_secs = min(1.0/60.0, 1.0/total_velocity)
        except:
            l_secs = 1.0/400.0

clock = pygame.time.Clock()
elapsed = 0
quit_p = False
mouse_pos = [0, 0]
mouse_left_down = False
pause = False
accumulator = 0.0
seconds = 1.0/60.0
simulation_speed = 1.0
acceleration_const = 5000.0
started = False
grab_offset = [0, 0]
clicked_my_dot = False
grid = False
selected = -3
space_toggle = False
while not quit_p:
    screen.fill((255, 255, 255))
    v_seconds = elapsed/1000.0*simulation_speed
    if started:
        accumulator += v_seconds
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_p = True
                break
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    quit_p = True
                    break
                if e.key == pygame.K_g:
                    grid = not grid
                if e.key == pygame.K_SPACE:
                    space_toggle = not space_toggle
                if e.key == pygame.K_KP_PLUS:
                    object_count += 1
                    objects.append(attractor())
                    objects[-1].pos = [0.0, 0.0]
                    objects[-1].sign = 1
                    objects[-1].charge = 1000.0
                    objects[-1].kind = "dot"
                if e.key == pygame.K_KP_MULTIPLY:
                    object_count += 1
                    objects.append(attractor())
                    objects[-1].pos = [0.0, 0.0]
                    objects[-1].sign = 1
                    objects[-1].charge = 1000.0
                    objects[-1].length = 200.0
                    objects[-1].alpha = 0.0
                    objects[-1].sin_a = 0.0
                    objects[-1].cos_a = 1.0
                    objects[-1].kind = "box"
                if e.key == pygame.K_s:
                    print object_count
                    print my_dot_pos[0], my_dot_pos[1]
                    print objective[0], objective[1]
                    for x in range(object_count):
                        if objects[x].kind == "dot":
                            print objects[x].pos[0], objects[x].pos[1], objects[x].charge, objects[x].sign
                        else:
                            print objects[x].pos[0], objects[x].pos[1], objects[x].charge, objects[x].sign, objects[x].length, objects[x].alpha

            if e.type == pygame.MOUSEBUTTONDOWN:
                keys = pygame.key.get_pressed()
                mouse_pos_old = pygame.mouse.get_pos()
                for x in range(object_count):
                    if objects[x].modify(mouse_pos_old, e.button, x, keys):
                        del objects[x]
                        object_count -= 1
                        break
                my_dot_pixels = coor_to_pixel(my_dot_pos)
                objective_pixels = coor_to_pixel(objective)
                if (mouse_pos_old[0]-my_dot_pixels[0])**2 + (mouse_pos_old[1]-my_dot_pixels[1])**2 < my_dot_mass**(2.0/3.0)*scale:
                    selected = -1
                if (mouse_pos_old[0]-objective_pixels[0])**2 + (mouse_pos_old[1]-objective_pixels[1])**2 < objective_size**(2.0/3.0)*scale:
                    selected = -2

            if e.type == pygame.MOUSEBUTTONUP:
                if e.button == 1:
                    selected = -3
                    if clicked_my_dot == True:
                        clicked_my_dot = False
                        started = True
            if e.type == pygame.MOUSEMOTION and clicked_my_dot and not started:
                mouse_pos = pygame.mouse.get_pos()
                my_dot_vel[0] = -(mouse_pos_old[0]-mouse_pos[0])/scale/10.0
                my_dot_vel[1] = (mouse_pos_old[1]-mouse_pos[1])/scale/10.0
                #my_dot_vel[0] = math.copysign(min(abs(my_dot_vel[0]), 100.0), my_dot_vel[0])
                #my_dot_vel[1] = math.copysign(min(abs(my_dot_vel[1]), 100.0), my_dot_vel[1])
        if pause == False:
            break

    if grid:
        for x in range(0, size[0], 20):
            pygame.draw.aaline(screen, (200, 200, 200), (x, 0), (x, size[1]))
        for y in range(0, size[1], 20):
            pygame.draw.aaline(screen, (200, 200, 200), (0, y), (size[0], y))

    if selected > -3:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = [mouse_pos[0], mouse_pos[1]]
        if grid:
            mouse_pos[0] = mouse_pos[0] - mouse_pos[0]%10
            mouse_pos[1] = mouse_pos[1] - mouse_pos[1]%10
        if selected == -2:
            objective = pixel_to_coor(mouse_pos)
        elif selected == -1 and not space_toggle:
            my_dot_pos = pixel_to_coor(mouse_pos)
        elif not space_toggle:
            objects[selected].pos = pixel_to_coor(mouse_pos)
            objects[selected].show_info()

    if space_toggle and pygame.mouse.get_pressed()[0]:
        my_dot_vel[0] = -(mouse_pos_old[0]-mouse_pos[0])/scale/10.0
        my_dot_vel[1] = (mouse_pos_old[1]-mouse_pos[1])/scale/10.0
        simulate(seconds, 4000, my_dot_vel, my_dot_pos)

    for i in range(object_count):
        objects[i].draw()

    pixel_points = coor_to_pixel(my_dot_pos)
    radius = int((my_dot_mass)**(1.0/3.0)*scale)
    gfxdraw.filled_circle(screen, pixel_points[0], pixel_points[1], radius, my_dot_color)
    if radius > 1:
        gfxdraw.aacircle(screen, pixel_points[0], pixel_points[1], radius, my_dot_color)
    if clicked_my_dot:
        pygame.draw.aaline(screen, (0, 0, 0), pixel_points, mouse_pos)

    #pixel_square_coors = coor_to_pixel([square[0], square[1]])
    #pixel_square_to = [square[2]/scale, square[3]/scale]
    #screen.fill((0, 255, 0), [pixel_square_coors[0], pixel_square_coors[1], pixel_square_to[0], pixel_square_to[1]])
    pixel_points = coor_to_pixel(objective)
    gfxdraw.filled_circle(screen, pixel_points[0], pixel_points[1], int((objective_size)**(1.0/3.0)*scale), (0, 255, 0))
    gfxdraw.aacircle(screen, pixel_points[0], pixel_points[1], int((objective_size)**(1.0/3.0)*scale), (0, 255, 0))

    pygame.display.update()
    elapsed = clock.tick(60)