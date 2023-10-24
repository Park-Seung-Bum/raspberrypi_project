import pygame
import random
import spidev
import time
import RPi.GPIO as GPIO

# GPIO 설정
green_led_pin = 15  # 초록 LED: GPIO15
red_led_pin = 14    # 빨간 LED: GPIO14

hearts = 3  # 시작 체력 개수

# 버튼 설정
button_pin = 4
flash_duration = 0.1  # 번쩍이는 효과 지속 시간 (초)
flash_color = (255, 255, 255)  # 번쩍이는 효과 색상


def flash_screen(screen, duration, color):
    """화면을 지정된 색상으로 지정된 시간 동안 번쩍입니다."""
    start_time = time.time()
    end_time = start_time + duration
    while time.time() < end_time:
        screen.fill(color)
        pygame.display.flip()
        pygame.time.delay(100)

# GPIO 초기화
GPIO.setmode(GPIO.BCM)
GPIO.setup(green_led_pin, GPIO.OUT)
GPIO.setup(red_led_pin, GPIO.OUT)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# SPI 설정
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 100000

# 초기화
pygame.init()

# 화면 크기 설정
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("장애물 피하기 게임")

# 색상 정의
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)

# 캐릭터 이미지 로드
character_images = {
    "left": [pygame.image.load("image/leftrun1.png"), pygame.image.load("image/leftrun3.png")],
    "right": [pygame.image.load("image/rightrun1.png"), pygame.image.load("image/rightrun3.png")],
}
character_direction = "right"  # 초기 방향 설정
character_index = 0
character_width = 50
character_height = 50
character_image = pygame.transform.scale(character_images[character_direction][character_index], (character_width, character_height))

# 이미지 변경 딜레이 설정
character_image_delay = 10 # 이미지 변경 딜레이 (프레임 단위)

# 폰트 설정
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 48)

# 함수: ADC 값 읽기
def readadc(adcnum):
    if adcnum > 7 or adcnum < 0:
        return -1
    r = spi.xfer2([1, (8 + adcnum) << 4, 0])
    data = ((r[1] & 3) << 8) + r[2]
    return data

# 함수: 포지션 계산
def position(adcnum, zerovalue):
    return readadc(adcnum) - zerovalue

xZero = 513
yZero = 520
tolerancevalue = 10

# 카운트다운 설정
countdown = 3
countdown_font = pygame.font.Font(None, 72)

# 게임 루프
clock = pygame.time.Clock()
running = True
game_over = False
bomb = 3
score = 0
fall_speed = 5

obstacles = []

def bomb_count(channel):
    print("bomb")

GPIO.add_event_detect(button_pin, GPIO.RISING, callback=bomb_count, bouncetime=300)

# 초기 캐릭터 위치 설정
character_x = width // 2 - 15
character_y = height - 50

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_over and event.type == pygame.MOUSEBUTTONDOWN:
            if width // 2 - 50 <= pygame.mouse.get_pos()[0] <= width // 2 + 50 and height // 2 + 50 <= pygame.mouse.get_pos()[1] <= height // 2 + 80:
                # Restart 버튼을 눌렀을 때 초기화
                game_over = False
                score = 0
                bomb = 3
                obstacles.clear()
                character_x = width // 2 - 15
                character_y = height - 50
                countdown = 3  # 카운트다운 초기화
                hearts =3
                
    sw_val = readadc(0)
    vrx_pos = position(1, xZero)
    vry_pos = position(2, yZero)

    if countdown > 0:
        # 카운트다운 중일 때
        screen.fill(black)
        countdown_text = countdown_font.render(str(countdown), True, white)
        countdown_rect = countdown_text.get_rect(center=(width // 2, height // 2))
        screen.blit(countdown_text, countdown_rect)
        pygame.display.flip()
        time.sleep(1)
        countdown -= 1
    else:
        # 게임 중일 때
        if (GPIO.event_detected(button_pin) and bomb > 0):
            obstacles.clear()
            bomb -= 1
            flash_screen(screen, flash_duration, flash_color)

        if vrx_pos < -tolerancevalue and character_x > 0:
            character_x -= 5
            character_direction = "left"
        elif vrx_pos > tolerancevalue and character_x < width - 30:
            character_x += 5
            character_direction = "right"

        # 이미지 변경 딜레이 체크
        if character_image_delay <= 0:
            character_index = (character_index + 1) % len(character_images[character_direction])
            character_image = pygame.transform.scale(character_images[character_direction][character_index], (character_width, character_height))
            character_image_delay = 7  # 딜레이 초기화
        else:
            character_image_delay -= 1

        for obstacle in obstacles:
            if "image" in obstacle:
                screen.blit(obstacle["image"], (obstacle["x"], obstacle["y"]))
            obstacle["y"] += fall_speed
            if obstacle["y"] > height:
                obstacles.remove(obstacle)
                if not game_over:
                    score += 1
            if character.colliderect(pygame.Rect(obstacle["x"], obstacle["y"], obstacle["width"], obstacle["height"])):
        # 생명력을 1 감소시킵니다.
                if not game_over:
                    hearts -= 1
                    flash_screen(screen, 0.03, red)
                    if hearts <= 0:
                # 생명력이 모두 소진되면 게임 오버로 설정
                        game_over = True
                    else:
                # 생명력이 남아있으면 장애물 제거
                        obstacles.remove(obstacle)

            
        if random.random() < 0.03:
            obstacle_width = random.randint(40, 120)
            obstacle_height = random.randint(20, 40)
            obstacle_x = random.randint(0, width - obstacle_width)
            obstacles.append({"x": obstacle_x, "y": 0, "width": obstacle_width, "height": obstacle_height})

        if score > 20:
            if random.random() < 0.005 + score / 1000:
                obstacle_width = random.randint(40, 120)
                obstacle_height = random.randint(20, 40)
                obstacle_x = random.randint(0, width - obstacle_width)
                obstacles.append({"x": obstacle_x, "y": 0, "width": obstacle_width, "height": obstacle_height})

        screen.fill(black)

        if game_over:
            game_over_text = large_font.render("Game Over", True, red)
            game_over_rect = game_over_text.get_rect(center=(width // 2, height // 2 - 30))
            screen.blit(game_over_text, game_over_rect)

            score_text = font.render("Your score: " + str(score), True, white)
            score_rect = score_text.get_rect(center=(width // 2, height // 2 + 30))
            screen.blit(score_text, score_rect)

            restart_text = font.render("Restart", True, white)
            restart_rect = restart_text.get_rect(center=(width // 2, height // 2 + 65))
            pygame.draw.rect(screen, black, (width // 2 - 50, height // 2 + 50, 100, 30))
            screen.blit(restart_text, restart_rect)
            GPIO.output(red_led_pin, GPIO.HIGH)
            GPIO.output(green_led_pin, GPIO.LOW)
        else:
            character = pygame.Rect(character_x, character_y, 30, 30)
            screen.blit(character_image, (character_x, character_y))
            GPIO.output(green_led_pin, GPIO.HIGH)
            GPIO.output(red_led_pin, GPIO.LOW)

            for obstacle in obstacles:
                pygame.draw.rect(screen, white, (obstacle["x"], obstacle["y"], obstacle["width"], obstacle["height"]))

            bomb_text = font.render("Bomb: " + str(bomb), True, white)
            screen.blit(bomb_text, (600, 10))

            score_text = font.render("Score: " + str(score), True, white)
            screen.blit(score_text, (10, 10))
            
            hearts_text = font.render("Hearts: " + str(hearts), True, white)
            screen.blit(hearts_text, (10, 500))
        pygame.display.flip()

    clock.tick(60)

GPIO.cleanup()
pygame.quit()
print("Game Over! Your score:", score)