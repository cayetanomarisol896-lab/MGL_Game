import pygame
import json
import os
import random

pygame.init()
W, H = 1000, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("ML_GAME ADVENTURES - Análisis y Diseño")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Consolas", 24, bold=True)
FONT_SMALL = pygame.font.SysFont("Consolas", 18)

# Colores estilo ML
BG = (13, 18, 35)
ACCENT = (0, 255, 213)
ACCENT2 = (122, 92, 255)
WHITE = (255, 255, 255)

# Guardado
SAVE_FILE = "record.json"
def load_record():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f).get("max", 0)
        except: return 0
    return 0

def save_record(score):
    record = load_record()
    if score > record:
        with open(SAVE_FILE, "w") as f:
            json.dump({"max": score}, f)

record_max = load_record()

class Player(pygame.Rect):
    def __init__(self):
        super().__init__(100, 300, 32, 32)
        self.vx = 0
        self.vy = 0
        self.vidas = 3
        self.puntos = 0
        self.on_ground = False
        self.tiempo = 90

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.vx = -5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vx = 5
        
        self.vy += 0.6  # gravedad
        if self.vy > 10: self.vy = 10

        self.x += self.vx
        self.collide(platforms, True)
        
        self.y += self.vy
        self.on_ground = False
        self.collide(platforms, False)

        # Limites
        if self.x < 0: self.x = 0
        if self.y > H: # cae fuera
            self.vidas -= 1
            self.x, self.y = 100, 300
            self.vy = 0

    def collide(self, platforms, horizontal):
        for p in platforms:
            if self.colliderect(p):
                if horizontal:
                    if self.vx > 0: self.right = p.left
                    if self.vx < 0: self.left = p.right
                else:
                    if self.vy > 0:
                        self.bottom = p.top
                        self.on_ground = True
                        self.vy = 0
                    else:
                        self.top = p.bottom
                        self.vy = 0

    def jump(self):
        if self.on_ground:
            self.vy = -13

class Dataset(pygame.Rect):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 20)
        self.collected = False

class Enemy(pygame.Rect):
    def __init__(self, x, y, range_x):
        super().__init__(x, y, 28, 28)
        self.start = x - range_x
        self.end = x + range_x
        self.dir = 1
    def update(self):
        self.x += self.dir * 2
        if self.x <= self.start or self.x >= self.end:
            self.dir *= -1

# Niveles
def crear_nivel(n):
    platforms = [
        pygame.Rect(0, H-40, W, 40),
        pygame.Rect(150, 450, 200, 20),
        pygame.Rect(400, 380, 200, 20),
        pygame.Rect(650, 300, 200, 20),
        pygame.Rect(100, 280, 150, 20),
    ]
    if n >= 2:
        platforms.append(pygame.Rect(300, 200, 180, 20))
    if n >= 3:
        platforms.append(pygame.Rect(500, 150, 150, 20))

    datasets = [Dataset(random.randint(150, 850), random.randint(100, 400)) for _ in range(8 + n*2)]
    enemies = [Enemy(200 + i*150, H-68, 60) for i in range(2+n)]
    portal = pygame.Rect(900, 200, 40, 60)
    return platforms, datasets, enemies, portal

# Juego principal
player = Player()
nivel = 1
platforms, datasets, enemies, portal = crear_nivel(nivel)
estado = "MENU"  # MENU, JUGANDO, PAUSA, GAMEOVER, VICTORIA
timer_event = pygame.USEREVENT+1
pygame.time.set_timer(timer_event, 1000)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == timer_event and estado == "JUGANDO":
            player.tiempo -= 1
            if player.tiempo <= 0:
                player.vidas = 0
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and estado == "JUGANDO": player.jump()
            if event.key == pygame.K_p and estado == "JUGANDO": estado = "PAUSA"
            if event.key == pygame.K_p and estado == "PAUSA": estado = "JUGANDO"
            if event.key == pygame.K_RETURN and estado == "MENU": 
                estado = "JUGANDO"
                player = Player()
                nivel = 1
                platforms, datasets, enemies, portal = crear_nivel(nivel)
            if event.key == pygame.K_r and estado in ["GAMEOVER", "VICTORIA"]:
                estado = "MENU"

    # Lógica
    if estado == "JUGANDO":
        player.update(platforms)
        for e in enemies: e.update()
        
        # Recolección
        for d in datasets:
            if not d.collected and player.colliderect(d):
                d.collected = True
                player.puntos += 10

        # Colisión enemigos
        for e in enemies:
            if player.colliderect(e):
                player.vidas -= 1
                player.x, player.y = 100, 300
                player.vy = 0
                pygame.time.delay(200)
                if player.vidas <= 0: break

        # Portal
        recolectados = sum(1 for d in datasets if d.collected)
        if recolectados >= len(datasets)*0.8 and player.colliderect(portal):
            if nivel < 3:
                nivel += 1
                platforms, datasets, enemies, portal = crear_nivel(nivel)
                player.x, player.y = 100, 300
                player.tiempo = 90
            else:
                estado = "VICTORIA"
                save_record(player.puntos)
                record_max = load_record()

        if player.vidas <= 0:
            estado = "GAMEOVER"
            save_record(player.puntos)
            record_max = load_record()

    # Dibujo
    screen.fill(BG)
    
    if estado == "MENU":
        title = FONT.render("ML_GAME ADVENTURES", True, ACCENT)
        screen.blit(title, (W//2 - title.get_width()//2, 100))
        sub = FONT_SMALL.render("Aventura Educativa - Recolecta Datasets y evita Bugs", True, WHITE)
        screen.blit(sub, (W//2 - sub.get_width()//2, 150))
        screen.blit(FONT_SMALL.render(f"Record: {record_max}", True, ACCENT2), (W//2-50, 200))
        screen.blit(FONT.render("[ENTER] Jugar  [ESC] Salir", True, WHITE), (W//2-200, 350))
        screen.blit(FONT_SMALL.render("Controles: A-D / Flechas mover, ESPACIO saltar, P pausa", True, WHITE), (W//2-280, 400))
        
        # Mini diagrama para exponer
        pygame.draw.rect(screen, (20,30,60), (100, 470, 800, 100), border_radius=10)
        pygame.draw.rect(screen, ACCENT, (100, 470, 800, 100), 2, border_radius=10)
        screen.blit(FONT_SMALL.render("Análisis y Diseño: RF1 Iniciar/Pausar | RF2 Movimiento | RF3 Colisiones | RF4 Puntaje", True, WHITE), (120, 490))
        screen.blit(FONT_SMALL.render("Arquitectura: Motor Pygame + Módulos Gráficos + Lógica + Entrada", True, WHITE), (120, 520))

    elif estado in ["JUGANDO", "PAUSA"]:
        # Plataformas
        for p in platforms:
            pygame.draw.rect(screen, (40, 50, 80), p, border_radius=5)
            pygame.draw.rect(screen, ACCENT2, p, 2, border_radius=5)
        # Datasets
        for d in datasets:
            if not d.collected:
                pygame.draw.rect(screen, ACCENT, d, border_radius=4)
                pygame.draw.rect(screen, WHITE, d, 1, border_radius=4)
        # Enemigos
        for e in enemies:
            pygame.draw.rect(screen, (255, 80, 80), e, border_radius=6)
            screen.blit(FONT_SMALL.render("BUG", True, WHITE), (e.x, e.y+5))
        # Portal
        pygame.draw.rect(screen, (255, 215, 0), portal, border_radius=8)
        screen.blit(FONT_SMALL.render("ML", True, BG), (portal.x+8, portal.y+20))
        # Player
        pygame.draw.rect(screen, WHITE, player, border_radius=8)
        pygame.draw.rect(screen, ACCENT, player, 2, border_radius=8)

        # HUD - ESTO ES LO QUE EL PROFE QUIERE VER
        hud_text = f"Nivel:{nivel} | Puntos:{player.puntos} | Vidas:{'♥'*player.vidas} | Tiempo:{player.tiempo}s | Datasets:{sum(1 for d in datasets if d.collected)}/{len(datasets)}"
        screen.blit(FONT_SMALL.render(hud_text, True, WHITE), (20, 10))
        screen.blit(FONT_SMALL.render(f"Record:{record_max}", True, ACCENT2), (W-150, 10))

        if estado == "PAUSA":
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            screen.blit(overlay, (0,0))
            t = FONT.render("PAUSA - [P] Continuar  [ESC] Salir", True, WHITE)
            screen.blit(t, (W//2 - t.get_width()//2, H//2))

    elif estado == "GAMEOVER":
        t = FONT.render(f"GAME OVER - Puntos: {player.puntos} - Record: {record_max}", True, (255,80,80))
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 50))
        screen.blit(FONT_SMALL.render("[R] Volver al Menú", True, WHITE), (W//2-80, H//2))

    elif estado == "VICTORIA":
        t = FONT.render(f"¡VICTORIA! Eres un ML Master - Score: {player.puntos}", True, ACCENT)
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 50))
        screen.blit(FONT_SMALL.render(f"Record guardado en {SAVE_FILE} - [R] Menú", True, WHITE), (W//2-150, H//2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()