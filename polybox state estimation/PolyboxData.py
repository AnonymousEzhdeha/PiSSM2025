
import pygame
import pymunk.pygame_util
import numpy as np
import os


class BallBox:
    def __init__(self, dt=0.2, res=(32, 32), init_pos=(3, 3), init_std=0, wall=None):
        pygame.init()

        self.dt = dt
        self.res = res
        if os.environ.get('SDL_VIDEODRIVER', '') == 'dummy':
            pygame.display.set_mode(res, 0, 24)
            self.screen = pygame.Surface(res, pygame.SRCCOLORKEY, 24)
            pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, res[0], res[1]), 0)
        else:
            self.screen = pygame.display.set_mode(res, 0, 24)
        self.gravity = (0.0, 0.0)
        self.initial_position = init_pos
        self.initial_std = init_std
        self.space = pymunk.Space()
        self.space.gravity = self.gravity
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.wall = wall
        self.static_lines = None

        self.dd = 2

    def _clear(self):
        self.screen.fill(pygame.color.THECOLORS["black"])

    def create_ball(self, radius=3):
        inertia = pymunk.moment_for_circle(1, 0, radius, (0, 0))
        body = pymunk.Body(1, inertia)
        position = np.array(self.initial_position) + self.initial_std * np.random.normal(size=(2,))
        position = np.clip(position, self.dd + radius +1, self.res[0]-self.dd-radius-1)
        body.position = position.tolist()

        shape = pymunk.Circle(body, radius, (0, 0))
        shape.elasticity = 1.0
        shape.color = pygame.color.THECOLORS["white"]
        return shape

    def fire(self, angle=50, velocity=20, radius=3):
        speedX = velocity * np.cos(angle * np.pi / 180)
        speedY = velocity * np.sin(angle * np.pi / 180)

        ball = self.create_ball(radius)
        ball.body.velocity = (speedX, speedY)

        self.space.add(ball, ball.body)
        return ball

    def run(self, iterations=20, sequences=500, angle_limits=(0, 360), velocity_limits=(10, 25), radius=3,
            flip_gravity=None, save=None, filepath='../../data/balls.npz', delay=None, shape=1):
        if save:
            images = np.empty((sequences, iterations, self.res[0], self.res[1]), dtype=np.float32)
            state = np.empty((sequences, iterations, 4), dtype=np.float32)

        dd = self.dd

        if shape==1:
            points = [(1, 8),
                      (1, 22),
                      (8, 30),
                      (22, 30),
                      (30, 22),
                      (30, 8),
                      (22, 1),
                      (8, 1),
                      (1, 8)]
        elif shape==2:
            points = [(3, 1),
                      (1, 15),
                      (8, 30),
                      (25, 30),
                      (30, 8),
                      (15, 1),
                      (3, 1)]

        # points = [[(1, 1), (1,31)],
        #           [(1, 1), (31, 1)],
        #           [(31, 31), (1, 31)],
        #           [(31, 31), (31, 1)],
        #           ]
        self.static_lines = []
        for i in range(len(points)-1):

            self.static_lines.append(pymunk.Segment(self.space.static_body, points[i], points[i+1], 0.0))
        # self.static_lines = [pymunk.Segment(self.space.static_body, (dd, dd), (dd, self.res[1]-dd), 0.0),
        #                      pymunk.Segment(self.space.static_body, (dd, dd), (self.res[0]-dd, dd), 0.0),
        #                      pymunk.Segment(self.space.static_body, (self.res[0] - dd, self.res[1] - dd),
        #                                     (dd, self.res[1]-dd), 0.0),
        #                      pymunk.Segment(self.space.static_body, (self.res[0] - dd, self.res[1] - dd),
        #                                     (self.res[0]-dd, dd), 0.0)]
        for line in self.static_lines:
            line.elasticity = 1.0
            line.color = pygame.color.THECOLORS["white"]
            self.space.add(line)

        for s in range(sequences):

            if s % 100 == 0:
                print(s)

            angle = np.random.uniform(*angle_limits)
            velocity = np.random.uniform(*velocity_limits)
            # controls[:, s] = np.array([angle, velocity])
            ball = self.fire(angle, velocity, radius)
            for i in range(iterations):
                self._clear()
                self.space.debug_draw(self.draw_options)
                self.space.step(self.dt)
                pygame.display.flip()

                if delay:
                    self.clock.tick(delay)

                if save == 'png':
                    pygame.image.save(self.screen, os.path.join(filepath, "bouncing_balls_%02d_%02d.png" % (s, i)))
                elif save == 'npz':
                    images[s, i] = pygame.surfarray.array2d(self.screen).swapaxes(1, 0).astype(np.float32) / (2**24 - 1)
                    state[s, i] = list(ball.body.position) + list(ball.body.velocity)

            # Remove the ball and the wall from the space
            self.space.remove(ball, ball.body)

        if save == 'npz':
            np.savez(os.path.abspath(filepath), images=images, state=state)


if __name__ == '__main__':
    os.environ['SDL_VIDEODRIVER'] = 'dummy'

    scale = 1

    np.random.seed(1234)

    # Create data dir
    if not os.path.exists('./Polybox state estimation/data'):
        os.makedirs('./Polybox state estimation/data')

    cannon = BallBox(dt=0.2, res=(32*scale, 32*scale), init_pos=(16*scale, 16*scale), init_std=2.5, wall=None)
    cannon.run(delay=None, iterations=20, sequences=5000, radius=3*scale, angle_limits=(0, 360), shape=2,
               velocity_limits=(10.0*scale, 15.0*scale), filepath='./Polybox state estimation/data/polygon.npz', save='npz')

    np.random.seed(5678)
    cannon = BallBox(dt=0.2, res=(32*scale, 32*scale), init_pos=(16*scale, 16*scale), init_std=2.5, wall=None)
    cannon.run(delay=None, iterations=20, sequences=1000, radius=3*scale, angle_limits=(0, 360), shape=2,
               velocity_limits=(10.0*scale, 15.0*scale), filepath='./Polybox state estimation/data/polygon_test.npz', save='npz')