import pygame
import math
from pygame import gfxdraw
import CoorsAndPixels
pygame.init()

#setup pygame stuff
size = [1600, 900]
screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
scale = min(size[0]/1600.0, size[1]/900.0)
print scale
font = pygame.font.Font("Atarian.ttf", 20)
levels_file = open("levels.txt")

level_thumbnails = []

object_count = 0 #number of objects (balls or bars) in level
objects = []
lines = []

#player information
my_dot_vel = [0.0, 0.0]
my_dot_pos = [-450.0, 0.0]
my_dot_color = [255, 0, 255]
my_dot_mass = 512.0
my_dot_image = pygame.image.load("my_ball.png").convert_alpha()
radius = int((my_dot_mass)**(1.0/3.0)*scale)
my_dot_image = pygame.transform.smoothscale(my_dot_image, (int(radius*2), int(radius*2)))

comments = []
scope_length = 0  #the length of the line drawn before shooting

#the large green dot
objective = [500.0, 0.0]
objective_size = 10000.0

#### stars will eventually be added
#stars = []
#star_image = pygame.image.load("star.png").convert_alpha()
#star_image = pygame.transform.smoothscale(star_image, (int(radius*5), int(radius*5)))

level_name = ""
acceleration_const = 5000.0


#the attractor class. can be a point charge (dot) or line
class attractor:
    def __init__(self):
        self.pos = [0.0, 0.0]
        self.sign = 1
        self.charge = 0.0
        self.kind = "" #"dot", "line"
        self.length = 0.0
        self.alpha = 0.0 #angle
        self.sin_a = 0.0
        self.cos_a = 0.0
        self.color = [255, 0, 0]

    #simulate the force on the ball
    def act_upon(self, d_time, local_vel, local_pos):
        global reset
        if self.kind == "dot": #point charge
            if (self.pos[0]-local_pos[0])**2+(self.pos[1]-local_pos[1])**2 < ((self.charge)**(1.0/3.0)+(my_dot_mass)**(1.0/3.0))**2:
                return False
            d_y = self.pos[1]-local_pos[1]
            d_x = self.pos[0]-local_pos[0]
            r = math.sqrt(d_x**2+d_y**2)
            s_a = d_y/1.0/r #sin
            c_a = d_x/1.0/r #cosine
            acceleration = acceleration_const/(d_y**2+d_x**2)*self.charge*self.sign
            if local_vel == False or local_vel == None:
                return False
            local_vel[0] += acceleration*c_a/1.0/r*d_time
            local_vel[1] += acceleration*s_a/1.0/r*d_time
        elif self.kind == "line": #line of charge
            #some pretty messy math. transformation of ball and line to the x axis
            t_x = local_pos[0]-self.pos[0]
            t_y = local_pos[1]-self.pos[1]
            r_x = t_x*self.cos_a + t_y*self.sin_a + self.pos[0]
            r_y = -t_x*self.sin_a + t_y*self.cos_a + self.pos[1]
            d_theta = self.pos[0] + self.length - r_x
            d_beta = r_x - self.pos[0]
            d_r = r_y-self.pos[1]

            #we check if the ball is touching the line
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

            #this comes straight from the integral for a finite line of charge
            #if the height difference between the line and ball is different than 0, no problem
            if d_r != 0.0:
                sin_theta = d_theta/math.sqrt(d_r**2+d_theta**2)
                sin_beta = d_beta/math.sqrt(d_r**2+d_beta**2)
                cos_theta = d_r/math.sqrt(d_r**2+d_theta**2)
                cos_beta = d_r/math.sqrt(d_r**2+d_beta**2)
                F_r_x = self.charge/4.0/math.pi/d_r*(cos_beta-cos_theta)*self.sign
                F_r_y = self.charge/4.0/math.pi/d_r*(sin_beta+sin_theta)*self.sign*(-1)
            #if they are at the same height, d_r = 0 so the the functions above return errors
            #here we just integrate with 0 height difference and change the sign if the ball is to the left or the right
            #(this is all done with the transformations to the x axis)
            else:
                a = self.pos[0]-r_x
                b = a+self.length
                F_r_x = self.charge/4.0/math.pi/a*self.sign - self.charge/4.0/math.pi/b*self.sign
                if r_x > self.pos[0]:
                    F_r_x *= -1
                F_r_y = 0.0
            #transform the relative forces to the real x and y axises.
            F_x = -F_r_y*self.sin_a + F_r_x*self.cos_a
            F_y = F_r_y*self.cos_a + F_r_x*self.sin_a
            if local_vel == False or local_vel == None:
                return False
            local_vel[0] += F_x*d_time
            local_vel[1] += F_y*d_time
        return [local_vel[0], local_vel[1]]

    #draw object
    def draw(self):
        if self.kind == "dot":
            pixel_points = CoorsAndPixels.coor_to_pixel(self.pos, scale, size)
            radius = int((self.charge)**(1.0/3.0)*scale)
            gfxdraw.filled_circle(screen, pixel_points[0], pixel_points[1], radius, self.color)
            if radius > 1:
                gfxdraw.aacircle(screen, pixel_points[0], pixel_points[1], radius, self.color)
        elif self.kind == "line":
            #pygame.draw.aaline(screen, self.color, CoorsAndPixels.coor_to_pixel(self.pos, scale, size, True), CoorsAndPixels.coor_to_pixel([self.pos[0]+self.length*self.cos_a, self.pos[1]+self.length*self.sin_a], scale, size, True))
            pygame.draw.line(screen, self.color, CoorsAndPixels.coor_to_pixel(self.pos, scale, size, True), CoorsAndPixels.coor_to_pixel([self.pos[0]+self.length*self.cos_a, self.pos[1]+self.length*self.sin_a], scale, size, True), int(self.charge**(1.0/3.0)/5.0)+1)

for line in levels_file:
    lines.append(line)
levels_file.close()
levels = []
#the levels are stored in a file and read here. it is a mess.
#first a "[" is found and so we start storing all the variables
#first line is level name, second is object_count, third is player position and fourth is objective position
#then come the objects. they are object_count lines.
#a point charge is "x y charge sign"
#a line charge is "x y charge sign length angle (with respect to x axis)"
#then come the comments, which are started with an *. "<text> x y"
#at the end comes the scope length
for i in range(len(lines)):
    if lines[i][0] == "[":
        levels.append([])
        tick = 1
        levels[-1].append(lines[i+tick]) #level name
        tick += 1
        levels[-1].append(int(lines[i+tick])) #object_count
        tick += 1
        levels[-1].append(map(float, lines[i+tick].split())) #my_dot_pos
        tick += 1
        levels[-1].append(map(float, lines[i+tick].split())) #objective_pos
        tick += 1
        for x in range(levels[-1][1]):
            levels[-1].append(map(float, lines[i+tick].split())) #dots_pos, dots_mass, neg (-1) or pos (1) force
            tick += 1
        levels[-1].append([]) #comments
        comment_count = 0
        while lines[i+tick][0] == "*":
            levels[-1][-1].append(lines[i+tick]) #comments
            comment_count += 1
            tick += 1
        levels[-1].append(comment_count)
        levels[-1].append(lines[i+tick]) #scope length
        tick += 1
        #this section adds stars, which haven't been added to levels yet
        if lines[i+tick] != "]\n":
            levels[-1].append([])
            for x in range(3):
                levels[-1][-1].append(map(float, lines[i+tick+x].split()))
            levels[-1].append(True)
        else:
            levels[-1].append(False)

#check which levels have been unlocked
#the level_locks.txt file stores lines of single 1s or 0s. A 1 is locked and 0 is unlocked
#if a level is won, the next level is automatically unlocked. The changes are written to the file
#at the end of the program
locks = []
with open('level_locks.txt', 'r') as lock_files:
    locks = lock_files.readlines()

def new_level(level):   #set all the variables to the desired level
    global capt
    capt = False
    #print levels[level]
    global clicked_my_dot
    clicked_my_dot = False
    global started
    started = False
    global level_name
    level_name = levels[level][0][:-1]
    global object_count
    object_count = levels[level][1]
    global my_dot_pos
    my_dot_pos = [levels[level][2][0], levels[level][2][1]]
    global my_dot_vel
    my_dot_vel = [0.0, 0.0]
    global objective
    objective = levels[level][3]
    global scope_length
    if levels[level][-1] == False:
        scope_length = int(levels[level][-2])
    else:
        scope_length = int(levels[level][-3])
    global objects
    objects = []
    global locks
    if locks[level] == "1\n":
        locks[level] = "0\n"
    for x in range(-1, object_count-1):
        #print levels[level][5+x]
        objects.append(attractor())
        objects[-1].pos = [levels[level][5+x][0], levels[level][5+x][1]]
        objects[-1].charge = levels[level][5+x][2]
        objects[-1].sign = levels[level][5+x][3]
        if objects[-1].sign == 1:
            objects[-1].color = [255, 0, 0]
        else:
            objects[-1].color = [0, 0, 255]
        try:
            objects[-1].length = levels[level][5+x][4]
            objects[-1].alpha = levels[level][5+x][5]
            objects[-1].sin_a = math.sin(objects[-1].alpha)
            objects[-1].cos_a = math.cos(objects[-1].alpha)
            objects[-1].kind = "line"
        except:
            objects[-1].kind = "dot"

    global comments
    comments = []
    if levels[level][-1] == False:
        counter = levels[level][-3]
    else:
        counter = levels[level][-4]
    for x in range(counter):
        comments.append(levels[level][4+object_count][x])
        comments[-1] = comments[-1][1:]
        comments[-1] = comments[-1].split()
        comments[-1][-1] = float(comments[-1][-1])
        comments[-1][-2] = float(comments[-1][-2])
        comments[-1][0] = ' '.join(comments[-1][:-2])
        comments[-1] = [comments[-1][0], [comments[-1][-2], comments[-1][-1]]]

    #stars will eventually be added
    #global stars
    #stars = []
    #if levels[level][-1] == True:
     #   for x in levels[level][-2]:
      #      stars.append(x)

def display_info(): #shows level name and comments (if there are any)
    label = font.render("Level " + str(level+1) + ": " + level_name, 1, (0, 0, 0))
    screen.blit(label, [10, 10])
    #label = font.render("Sim. speed: " + str(simulation_speed), 1, (0, 0, 0))
    #screen.blit(label, [10, 10+label.get_rect()[3]])
    for x in comments:
        label = font.render(x[0], 1, (0, 0, 0))
        screen.blit(label, CoorsAndPixels.coor_to_pixel([x[1][0], x[1][1]], scale, size))

#this function shows the path that the ball will take
#its length is regulated by the amount of steps, but it varies with how fast the ball is going
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
        pygame.draw.aaline(screen, (255, green, blue), CoorsAndPixels.coor_to_pixel(prev_dots, scale, size, True), CoorsAndPixels.coor_to_pixel(local_pos, scale, size, True))
        total_velocity = math.sqrt(local_vel[0]**2 + local_vel[1]**2)
        try:
            l_secs = min(1.0/60.0, 1.0/total_velocity)
        except:
            l_secs = 1.0/400.0

clock = pygame.time.Clock()
in_menu = True
level = 0
new_level(level)

menu = 0 #0 = main menu, 1 = level select menu
start_rect = [size[0]/2-100, size[1]/2-40, 200, 30] #main menu start button
level_rect = [size[0]/2-100, size[1]/2-0, 200, 30] #main menu level select button
level_select = -2
selected = False

w = 200 #size of squares in the level select menu in pixels
s = 30 #spacing between squares in pixels
n = int(size[0])/(w+s) #number of boxes that fit in a row
f = int((size[0]-w*n-s*(n-1))/2) #spacing from the borders of the screen (vertical borders)
for x in range(len(levels)): #load the level thumbnails
    if locks[x] == "0\n":
        try: #if unlocked and the thumbnail for that level is found
            level_thumbnails.append(pygame.image.load(str(x) + ".png").convert_alpha())
        except: #if unlocked and the thumbnail is not found
            level_thumbnails.append(pygame.image.load("question.png").convert_alpha())
    else: #if locked
        level_thumbnails.append(pygame.image.load("locked.png").convert_alpha())
    level_thumbnails[x] = pygame.transform.smoothscale(level_thumbnails[x], (w, w))

quit_p = False #main loop condition

#main menu
while in_menu:
    mouse_pos = pygame.mouse.get_pos()
    screen.fill((255, 255, 255))

    if menu == 0: #main menu
        if CoorsAndPixels.in_box(mouse_pos, start_rect):
            label = font.render("Start", 1, (0, 255, 0))
            pygame.draw.rect(screen, (0, 255, 0), start_rect, 1)
        else:
            label = font.render("Start", 1, (0, 0, 0))
        label_rect = label.get_rect()
        label_rect[0] = (size[0]-label_rect[2])/2
        label_rect[1] = start_rect[1]+(30-label_rect[3])/2
        screen.blit(label, label_rect)

        if CoorsAndPixels.in_box(mouse_pos, level_rect):
            label = font.render("Level select", 1, (0, 255, 0))
            pygame.draw.rect(screen, (0, 255, 0), level_rect, 1)
        else:
            label = font.render("Level select", 1, (0, 0, 0))
        label_rect = label.get_rect()
        label_rect[0] = (size[0]-label_rect[2])/2
        label_rect[1] = level_rect[1]+(30-label_rect[3])/2
        screen.blit(label, label_rect)

    elif menu == 1: #level select menu
        screen.fill((255, 255, 255))
        selected = False
        for x in range(len(levels)):
            pos_x = f+w*(x%n)+s*(x%n)
            pos_y = s*(x/n+1)+w*(x/n)
            screen.blit(level_thumbnails[x], [pos_x, pos_y])
            if CoorsAndPixels.in_box(mouse_pos, [pos_x, pos_y, w, w]):
                selected = True
                level_select = x
                if locks[x] == "0\n":
                    pygame.draw.rect(screen, (0, 255, 0), [pos_x, pos_y, w, w], 1)
                else:
                    pygame.draw.rect(screen, (255, 0, 0), [pos_x, pos_y, w, w], 1)
            else:
                pygame.draw.rect(screen, (0, 0, 0), [pos_x, pos_y, w, w], 1)
            label = font.render(str(x+1), 1, (0, 0, 0))
            label_rect = label.get_rect()
            #label_rect[0] = pos_x+w/2-label_rect[2]/2
            #label_rect[1] = pos_y+w/2-label_rect[3]/2
            label_rect[0] = pos_x+10
            label_rect[1] = pos_y+10
            screen.blit(label, label_rect)
        label = font.render("Back", 1, (0, 0, 0)) #back button
        screen.blit(label, [15, 5])
        if CoorsAndPixels.in_box(mouse_pos, [15, 5, label.get_rect()[2], label.get_rect()[3]]):
            pygame.draw.rect(screen, (0, 255, 0), [15, 5, label.get_rect()[2], label.get_rect()[3]], 1)
            level_select = -1
            selected = True
        if selected == False:
            level_select = -2

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            quit_p = True
            in_menu = False
            break
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                quit_p = True
                in_menu = False
                break
        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if CoorsAndPixels.in_box(mouse_pos, start_rect) and menu == 0: #start at the first level
                    in_menu = False
                    new_level(0)
                if CoorsAndPixels.in_box(mouse_pos, level_rect) and menu == 0: #go to level select menu
                    menu = 1
                if level_select > -1: #start at the selected menu
                    if locks[level_select] == "0\n":
                        new_level(level_select)
                        level = level_select
                        in_menu = False
                        break
                elif level_select == -1: #go back to main menu
                    selected = False
                    level_select = -2
                    menu = 0
                    break

    pygame.display.update()

mouse_pos = [0, 0]
mouse_pos_old = [0, 0]
mouse_left_down = False
pause = False
simulation_speed = 10.0      #the higher this value, the more steps that are taken in the simulation per screen refresh
started = False  #true once the ball is shot
clicked_my_dot = False #true while the player is pointing the ball
elapsed = 0  #time taken per tick
accumulator = 0.0 #this is for a deterministic physics simulation, but variable refresh rate (fix your timestep ftw)
seconds = 1.0/60.0 #delta time taken in simulation, which varies according to ball speed
while not quit_p:
    v_seconds = elapsed/1000.0*simulation_speed
    if started:
        accumulator += v_seconds
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            quit_p = True
            break
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                quit_p = True
                break
            if e.key == pygame.K_KP_PLUS: #increase simulation speed
                if simulation_speed < 0.1:
                    simulation_speed += 0.1
                else:
                    sim_add = 10**math.floor(math.log10(simulation_speed)+1.0)/10.0
                    simulation_speed += sim_add
            if e.key == pygame.K_KP_MINUS: #decrease simulation speed
                sim_add = 10**math.floor(math.log10(simulation_speed)+1.0)/10.0
                if sim_add == simulation_speed:
                    simulation_speed -= sim_add/10.0
                else:
                    simulation_speed -= sim_add
                if sim_add < 0.1:
                    sim_add = 0.0
            if e.key == pygame.K_r: #restart at the current level
                new_level(level)
        #mouse events
        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1: #left click
                mouse_pos_old = pygame.mouse.get_pos()
                my_dot_pixels = CoorsAndPixels.coor_to_pixel(my_dot_pos, scale, size)
                #if ball is clicked
                if (mouse_pos_old[0]-my_dot_pixels[0])**2+(mouse_pos_old[1]-my_dot_pixels[1])**2 < (my_dot_mass**(1.0/3.0)*scale)**2 and not started:
                    clicked_my_dot = True
            if e.button == 3: #cancel shot by right clicking
                if clicked_my_dot:
                    clicked_my_dot = False
        if e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1: #shoot the ball
                if clicked_my_dot == True:
                    clicked_my_dot = False
                    started = True
        if e.type == pygame.MOUSEMOTION and clicked_my_dot and not started: #adjust velocity for the shoot
            mouse_pos = pygame.mouse.get_pos()
            my_dot_vel[0] = -(mouse_pos_old[0]-mouse_pos[0])/scale/10.0
            my_dot_vel[1] = (mouse_pos_old[1]-mouse_pos[1])/scale/10.0
            #my_dot_vel[0] = math.copysign(min(abs(my_dot_vel[0]), 100.0), my_dot_vel[0])
            #my_dot_vel[1] = math.copysign(min(abs(my_dot_vel[1]), 100.0), my_dot_vel[1])

    screen.fill((255, 255, 255))

    if not started and clicked_my_dot: #simulate and draw the orbit
            simulate(seconds, scope_length, my_dot_vel, my_dot_pos)#min(dot_count*100, 1800)
    if started:
        while accumulator >= seconds: #straight from fix your timestep. fixed physics timestep, variable screen refesh rate
            reset = False
            for i in range(object_count):
                my_dot_vel = objects[i].act_upon(seconds, my_dot_vel, my_dot_pos)
                if my_dot_vel == False: #if the ball crashes into something, the velocity is return as False to restart the level
                    new_level(level)
            if reset:
                break
            my_dot_pos[0] += my_dot_vel[0]*seconds #update x pos
            my_dot_pos[1] += my_dot_vel[1]*seconds #update y pos
            #if hit objective
            if (objective[0]-my_dot_pos[0])**2+(objective[1]-my_dot_pos[1])**2 < ((objective_size)**(1.0/3.0)+(my_dot_mass)**(1.0/3.0))**2:
                level += 1
                if level >= len(levels):
                    quit_p = True
                    break
                new_level(level)
            #the time step is fixed according to velocity
            total_velocity = math.sqrt(my_dot_vel[0]**2 + my_dot_vel[1]**2)
            try:
                seconds = min(1.0/60.0, 1.0/total_velocity)
            except:
                seconds = 1.0/400.0
            accumulator -= seconds

    #draw objects
    for i in range(object_count):
        objects[i].draw()

    #for x in stars:
     #   pixel_pos = CoorsAndPixels.coor_to_pixel(x, scale, size)
      #  screen.blit(star_image, [int(pixel_pos[0]-radius*2.5), int(pixel_pos[1]-radius*2.5)])

    #draw player ball
    pixel_points = CoorsAndPixels.coor_to_pixel(my_dot_pos, scale, size, True)
    screen.blit(my_dot_image, [pixel_points[0]-radius, pixel_points[1]-radius])

    #gfxdraw.filled_circle(screen, pixel_points[0], pixel_points[1], radius, my_dot_color)
    #if radius > 1:
    #    gfxdraw.aacircle(screen, pixel_points[0], pixel_points[1], radius, my_dot_color)

    #draw line if aiming to shoot
    if clicked_my_dot:
        pygame.draw.aaline(screen, (0, 0, 0), pixel_points, mouse_pos)

    #pixel_square_coors = coor_to_pixel([square[0], square[1]])
    #pixel_square_to = [square[2]/scale, size, square[3]/scale]
    #screen.fill((0, 255, 0), [pixel_square_coors[0], pixel_square_coors[1], pixel_square_to[0], pixel_square_to[1]])
    #draw objective
    pixel_points = CoorsAndPixels.coor_to_pixel(objective, scale, size)
    gfxdraw.filled_circle(screen, pixel_points[0], pixel_points[1], int((objective_size)**(1.0/3.0)*scale), (0, 255, 0))
    gfxdraw.aacircle(screen, pixel_points[0], pixel_points[1], int((objective_size)**(1.0/3.0)*scale), (0, 255, 0))

    display_info()
    pygame.display.update()
    elapsed = clock.tick(60) #60 hz refresh rate

#save level locks
with open("level_locks.txt", 'w') as lock_files:
    lock_files.writelines(locks)