import pygame
import neat
import os
import random

pygame.font.init()

# Constants for window dimensions and generation count
WIN_WIDTH = 500
WIN_HEIGHT = 800
GEN = 0

# Font for displaying scores and generation count
STAT_FONT = pygame.font.SysFont('comicsans', 50)

# Load images for birds, pipes, base, and background
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bird3.png")))]
PIPE_IMG = [pygame.transform.scale2x(pygame.image.load(os.path.join("images", "pipe.png")))]
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("images", "bg.png")))


# Class representing the bird object
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25  # Maximum rotation angle
    ROTATION_SPEED = 20
    ANIMATION_TIME = 5  # Time for each frame in animation cycle

    def __init__(self, x, y):
        # Initialize bird attributes
        self.x = x
        self.y = y
        self.tilt = 0
        self.tickCount = 0
        self.speed = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    # Method for bird's jump
    def jump(self):
        self.speed = -10.5
        self.tickCount = 0
        self.height = self.y

    # Update bird's position and tilt based on movement physics
    def move(self):
        self.tickCount += 1
        d = self.speed * self.tickCount + 1.5 * self.tickCount ** 2  # Physics formula
        if d >= 16:  # Cap downward velocity
            d = 16
        if d < 0:  # Add a small boost when moving upwards
            d -= 2
        self.y = self.y + d

        # Adjust tilt based on movement direction
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_SPEED

    # Draw the bird with rotation
    def draw(self, win):
        self.img_count += 1
        # Animation cycling
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If diving, keep a fixed frame
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_img, new_rect.topleft)

    # Get collision mask for bird
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


# Class representing the pipes
class Pipe:
    GAP = 200  # Space between top and bottom pipes
    VEL = 5  # Pipe movement speed

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG[0], False, True)
        self.PIPE_BOTTOM = PIPE_IMG[0]
        self.passed = False
        self.set_height()

    # Randomize pipe height
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # Move pipes to the left
    def move(self):
        self.x -= self.VEL

    # Draw pipes
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Check if bird collides with pipes
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        return bool(t_point or b_point)


# Class for the moving base
class Base:
    VEL = 5  # Speed of the base
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    # Move the base for seamless looping
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # Draw the base
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# Function to draw all game components in the window
def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0, 0))  # Draw background
    for pipe in pipes:
        pipe.draw(win)  # Draw each pipe
    # Display score and generation count
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))
    base.draw(win)  # Draw the base
    for bird in birds:
        bird.draw(win)  # Draw each bird
    pygame.display.update()


# Main function for NEAT algorithm
def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    # Initialize neural networks and genomes
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    score = 0

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)  # Set FPS to 30
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # Determine which pipe to consider
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        # Update birds based on neural network output
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1  # Reward for staying alive
            output = nets[x].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        # Manage pipes and score
        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):  # Check collision
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()

        if add_pipe:  # Add new pipe when passed
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:  # Remove off-screen pipes
            pipes.remove(r)

        # Remove birds if they hit the ground or go off-screen
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() > 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()  # Move base
        draw_window(win, birds, pipes, base, score, GEN)  # Update display


# Run the NEAT algorithm
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    p = neat.Population(config)  # Initialize population
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(main, 50)  # Run NEAT for 50 generations


if __name__ == '__main__':
    local_directory = os.path.dirname(__file__)
    config_path = os.path.join(local_directory, 'configfile.txt')
    run(config_path)