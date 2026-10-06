import pygame
import random
import math

WIDTH = 800
HEIGHT = 600
MISSILE_SPEED = 7

DETECTION_RANGE = 300

FOV_THRESHOLD = 0.7

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)

class Player:
    def __init__(self):
        self.color = (255, 255, 255)
        self.position = pygame.Vector2(WIDTH/2,HEIGHT/2)
        self.velocity = pygame.Vector2(0,0)
        self.acceleration = 0
        self.angle = 0
        self.thrust = 0

    def turn(self, x):
        self.angle += x

    def draw(self, screen):
        front = self.position + pygame.Vector2(20, 0).rotate(self.angle)
        left = self.position + pygame.Vector2(-15, -12).rotate(self.angle)
        right = self.position + pygame.Vector2(-15, 12).rotate(self.angle)
        pygame.draw.polygon(screen, (255, 0, 0), [front, left, right])

    def move(self):
        acceleration = pygame.Vector2(self.thrust * math.cos(math.radians(self.angle)), self.thrust*math.sin(math.radians(self.angle)))
        self.position += acceleration
        if self.position.x > WIDTH:
            self.position.x = 0

        if self.position.x < 0:
            self.position.x = WIDTH

        if self.position.y > HEIGHT:
            self.position.y = 0

        if self.position.y < 0:
            self.position.y = HEIGHT


class Enemy:
    def __init__(self):
        self.position = pygame.Vector2(
            WIDTH / 4,
            HEIGHT / 2
        )
        self.angle = 0
        self.state = "PATROL"
        self.color = WHITE

    def draw(self, screen):
        front = self.position + pygame.Vector2(20, 0).rotate(-self.angle)
        left = self.position + pygame.Vector2(-15, -12).rotate(-self.angle)
        right = self.position + pygame.Vector2(-15, 12).rotate(-self.angle)
        pygame.draw.polygon(screen, self.color, [front, left, right])


class Asteroid:
    def __init__(self):
        self.radius = random.randint(15, 50)
        self.mass = self.radius * self.radius
        self.position = pygame.Vector2(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
        dx = random.uniform(-4, 4)
        dy = random.uniform(-4, 4)
        self.velocity = pygame.Vector2(dx, dy)
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


    def move(self):
        self.position += self.velocity

        if self.position.x < -self.radius:
            self.position.x = WIDTH + self.radius
        if self.position.x > WIDTH + self.radius:
            self.position.x = -self.radius
        if self.position.y < -self.radius:
            self.position.y = HEIGHT + self.radius
        if self.position.y > HEIGHT + self.radius:
            self.position.y = -self.radius

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)


class Missile:
    def __init__(self, location):
        self.position = pygame.Vector2(location)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = 5

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), self.position, self.radius)


def bounce(a, b):
    normal = b.position - a.position
    distance = normal.length()

    if distance == 0 or distance > a.radius + b.radius:
        return

    normal = normal / distance

    overlap = a.radius + b.radius - distance
    a.position -= normal * (overlap / 2)
    b.position += normal * (overlap / 2)

    speed = (a.velocity - b.velocity).dot(normal)

    impulse = 2 * speed / (a.mass + b.mass)
    a.velocity -= normal * impulse * b.mass
    b.velocity += normal * impulse * a.mass


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Enemy Detection System")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 30)

missiles = []
enemy_missiles = []
enemy_timer = 0

asteroids = []
for n in range(8):
    rock = Asteroid()
    touching = True
    while touching:
        touching = False
        for other in asteroids:
            if rock.position.distance_to(other.position) < rock.radius + other.radius:
                touching = True
                rock.position = pygame.Vector2(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
    asteroids.append(rock)

player = Player()
enemy = Enemy()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            missiles.append(Missile(player.position))
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        player.turn(-5)
    if keys[pygame.K_d]:
        player.turn(5)
    if keys[pygame.K_w]:
        player.thrust += .3
    else:
        player.thrust = max(0, player.thrust -.09)
    player.move()

    enemy.angle += 0.5

    radians = math.radians(enemy.angle)

    enemy_forward = pygame.Vector2(
        math.cos(radians),
        -math.sin(radians)
    )

    to_player = (
        player.position - enemy.position
    )

    if to_player.length() > 0:
        to_player = to_player.normalize()

    distance = enemy.position.distance_to(
        player.position
    )

    dot = enemy_forward.dot(
        to_player
    )

    if (
        distance < DETECTION_RANGE
        and dot > FOV_THRESHOLD
    ):
        detected = True

    else:
        detected = False

    if detected:
        enemy.state = "ATTACK"
        enemy.color = RED
    else:
        enemy.state = "PATROL"
        enemy.color = WHITE

    enemy_timer += 1
    if detected == True and enemy_timer > 30:
        direction = (
            player.position - enemy.position
        ).normalize()

        missile_velocity = (
            direction * MISSILE_SPEED
        )

        enemy_missile = Missile(enemy.position)
        enemy_missile.velocity = missile_velocity
        enemy_missiles.append(enemy_missile)
        enemy_timer = 0

    for enemy_missile in enemy_missiles:
        enemy_missile.position += enemy_missile.velocity

    for rock in asteroids:
        rock.move()

    for i in range(len(asteroids)):
        for j in range(i + 1, len(asteroids)):
            bounce(asteroids[i], asteroids[j])

    for missile in missiles:
        nearest = min(
            asteroids,
            key=lambda asteroid:
                missile.position.distance_to(asteroid.position)
        )
        direction = nearest.position - missile.position
        direction = direction.normalize()
        missile.velocity = direction * MISSILE_SPEED
        missile.position += missile.velocity
        for asteroid in asteroids:
            distance = missile.position.distance_to(asteroid.position)
            if distance < missile.radius + asteroid.radius:
                asteroids.remove(asteroid)
                asteroids.append(Asteroid())
                missiles.remove(missile)
                break

    distance = enemy.position.distance_to(
        player.position
    )

    screen.fill((0, 0, 0))
    for rock in asteroids:
        rock.draw(screen)
    for missile in missiles:
        missile.draw(screen)
    for enemy_missile in enemy_missiles:
        enemy_missile.draw(screen)

    pygame.draw.circle(
        screen,
        GRAY,
        enemy.position,
        DETECTION_RANGE,
        1
    )

    pygame.draw.line(
        screen,
        RED,
        enemy.position,
        enemy.position + enemy_forward * 100,
        3
    )

    enemy.draw(screen)
    player.draw(screen)

    if detected:
        status_text = font.render("Enemy: PLAYER DETECTED!", True, RED)
    else:
        status_text = font.render("Enemy: PATROL", True, WHITE)

    distance_text = font.render(
        f"Distance: {distance:.1f}",
        True,
        WHITE
    )

    dot_text = font.render(
        f"Dot Product: {dot:.2f}",
        True,
        WHITE
    )

    state_text = font.render(
        f"Enemy State: {enemy.state}",
        True,
        WHITE
    )

    screen.blit(status_text, (10, 10))
    screen.blit(distance_text, (10, 40))
    screen.blit(dot_text, (10, 70))
    screen.blit(state_text, (10, 100))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
