import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
BOARD_WIDTH, BOARD_HEIGHT = 800, 800
PANEL_WIDTH = 400
WIDTH, HEIGHT = BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT
ROWS, COLS = 12, 12
SQUARE_SIZE = BOARD_HEIGHT // ROWS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
SPECIAL_RED = (255, 105, 180)  # Pink for red player knight
SPECIAL_BLUE = (135, 206, 250)  # Light blue for blue player knight
HIGHLIGHT = (173, 216, 230)  # Light blue for highlighting valid cells

LIGHT_RED = (255, 182, 193)
LIGHT_BLUE = (173, 216, 230)

# Screen setup
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('12x12 Checkers Game')


class Piece:
    PADDING = 15
    OUTLINE = 2

    def __init__(self, row, col, color, is_king=False, is_knight=False):
        self.row = row
        self.col = col
        self.color = color
        self.king = is_king
        self.knight = is_knight
        self.x = 0
        self.y = 0
        self.calc_pos()

    def calc_pos(self):
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - self.PADDING
        pygame.draw.circle(win, GREY, (self.x, self.y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            pygame.draw.circle(win, YELLOW, (self.x, self.y), radius // 2)
        if self.knight:
            pygame.draw.circle(win, GREEN, (self.x, self.y), radius // 3)

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()


class Board:
    def __init__(self):
        self.board = []
        self.selected_piece = None
        self.turn = RED
        self.valid_moves = {}
        self.red_captures = 0
        self.blue_captures = 0
        self.red_points = 0
        self.blue_points = 0
        self.red_knight_set = False
        self.blue_knight_set = False
        self.setup_phase = True
        self.winner = None
        self.red_boxes = []
        self.blue_boxes = []
        self.placing_box = False
        self.create_board()
        self.start_time = time.time()  # Start the timer

    def draw_squares(self, win):
        win.fill(BLACK)
        for row in range(ROWS):
            for col in range(row % 2, COLS, 2):
                pygame.draw.rect(win, WHITE, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def create_board(self):
        self.board = []
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if row % 2 == ((col + 1) % 2):
                    if row < 4:
                        self.board[row].append((Piece(row, col, RED), RED))
                    elif row > 7:
                        self.board[row].append((Piece(row, col, BLUE), BLUE))
                    else:
                        self.board[row].append((0, None))
                else:
                    self.board[row].append((0, None))

        # Knight pieces will be placed during the setup phase
        self.red_knight = Piece(-1, -1, SPECIAL_RED, is_knight=True)
        self.blue_knight = Piece(-1, -1, SPECIAL_BLUE, is_knight=True)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece, color = self.board[row][col]
                if isinstance(piece, int) and piece == 1:
                    if color == RED:
                        pygame.draw.rect(win, LIGHT_RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                    else:
                        pygame.draw.rect(win, LIGHT_BLUE, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                elif piece != 0:
                    piece.draw(win)
        if self.red_knight_set:
            self.red_knight.draw(win)
        if self.blue_knight_set:
            self.blue_knight.draw(win)
        if self.setup_phase:
            self.highlight_valid_cells(win)
        self.draw_valid_moves(win)
        self.draw_panel(win)

    def move(self, piece, row, col):
        self.board[piece.row][piece.col] = (0, None)  # Clear the old position
        if (piece.color == RED and row == ROWS - 1) or (piece.color == BLUE and row == 0):
            if piece.color == RED:
                self.red_points += 1
            else:
                self.blue_points += 1
            piece.move(-1, -1)  # Move piece off the board
            self.check_winner()
        else:
            self.board[row][col] = (piece, piece.color)  # Move the piece to the new position
            piece.move(row, col)

    def get_piece(self, row, col):
        piece, color = self.board[row][col]
        return piece

    def draw_valid_moves(self, win):
        for move in self.valid_moves:
            row, col = move
            pygame.draw.circle(win, GREEN, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)

    def highlight_valid_cells(self, win):
        if self.turn == RED and not self.blue_knight_set:
            for row in range(ROWS - 3, ROWS):
                for col in range(COLS):
                    if self.board[row][col] == (0, None):
                        pygame.draw.rect(win, HIGHLIGHT, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        elif self.turn == BLUE and not self.red_knight_set:
            for row in range(3):
                for col in range(COLS):
                    if self.board[row][col] == (0, None):
                        pygame.draw.rect(win, HIGHLIGHT, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def select(self, row, col):
        if self.winner:
            return

        if self.setup_phase:
            if self.turn == RED and not self.blue_knight_set:
                # Red places the blue knight in rows 9-11 (blue starting area)
                if row >= ROWS - 3 and self.board[row][col] == (0, None):
                    self.board[row][col] = (self.blue_knight, BLUE)
                    self.blue_knight.move(row, col)
                    self.blue_knight_set = True
                    self.turn = BLUE
                    return True
            elif self.turn == BLUE and not self.red_knight_set:
                # Blue places the red knight in rows 0-2 (red starting area)
                if row < 3 and self.board[row][col] == (0, None):
                    self.board[row][col] = (self.red_knight, RED)
                    self.red_knight.move(row, col)
                    self.red_knight_set = True
                    self.turn = RED
                    self.setup_phase = False
                    return True
            return False

        if self.placing_box:
            if self.board[row][col] == (0, None):
                self.board[row][col] = (1, self.turn)
                if self.turn == RED:
                    self.red_boxes.append(((row, col), 6))
                else:
                    self.blue_boxes.append(((row, col), 6))
                self.placing_box = False
                self.change_turn()
                return True

        if self.selected_piece:
            result = self._move(row, col)
            if not result:
                self.selected_piece = None
                self.select(row, col)

        piece = self.get_piece(row, col)
        if isinstance(piece, Piece) and (piece.color == self.turn or (piece.color == SPECIAL_RED and self.turn == RED) or (piece.color == SPECIAL_BLUE and self.turn == BLUE)):
            self.selected_piece = piece
            self.valid_moves = self.get_valid_moves(piece)
            return True

        return False

    def _move(self, row, col):
        if self.selected_piece and (row, col) in self.valid_moves:
            skipped = self.valid_moves[(row, col)]
            self.move(self.selected_piece, row, col)
            if skipped:
                self.remove(skipped)
            self.change_turn()
            self.check_winner()
        else:
            return False

        return True

    def change_turn(self):
        self.valid_moves = {}
        if self.turn == RED:
            self.turn = BLUE
        else:
            self.turn = RED
        self.update_boxes()

    def update_boxes(self):
        print(self.red_boxes, self.blue_boxes)
        for i, (position, turns) in enumerate(self.red_boxes[:]):
            if turns > 1:
                self.red_boxes[i] = (position, turns - 1)
            else:
                row, col = position
                self.board[row][col] = (0, None)
                self.red_boxes.pop(i)

        for i, (position, turns) in enumerate(self.blue_boxes[:]):
            if turns > 1:
                self.blue_boxes[i] = (position, turns - 1)
            else:
                row, col = position
                self.board[row][col] = (0, None)
                self.blue_boxes.pop(i)

    def remove(self, pieces):
        for piece in pieces:
            if isinstance(piece, Piece):
                if piece.color == RED or piece.color == SPECIAL_RED:
                    self.blue_captures += 1
                else:
                    self.red_captures += 1

                if self.selected_piece.knight:
                    # Place the knight in the captured piece's position
                    self.board[piece.row][piece.col] = (self.selected_piece, self.selected_piece.color)
                    if piece.knight:
                        # If the captured piece is a knight, reset its position to -1, -1
                        piece.move(-1, -1)
                else:
                    self.board[piece.row][piece.col] = (0, None)
                    if piece.knight:
                        # If the captured piece is a knight, reset its position to -1, -1
                        piece.move(-1, -1)

    def get_valid_moves(self, piece):
        moves = {}
        if piece.knight:
            moves.update(self._knight_moves(piece))
        else:
            row = piece.row
            col = piece.col

            if piece.color == BLUE or piece.color == SPECIAL_BLUE or piece.king:
                moves.update(self._traverse_forward(row - 1, max(row - 3, -1), -1, piece.color, col))
            if piece.color == RED or piece.color == SPECIAL_RED or piece.king:
                moves.update(self._traverse_forward(row + 1, min(row + 3, ROWS), 1, piece.color, col))

        return moves

    def _traverse_forward(self, start, stop, step, color, col, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if col < 0 or col >= COLS:
                break

            current, current_color = self.board[r][col]

            if current == 1:  # Encountered a blocking box
                break

            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, col)] = last + skipped
                else:
                    moves[(r, col)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, -1)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_forward(r + step, row, step, color, col, skipped=last))
                break
            elif isinstance(current, Piece) and current.color == color:
                break
            else:
                last = [current]

        return moves

    def _knight_moves(self, piece):
        moves = {}
        directions = [
            (2, 1), (1, 2), (-1, 2), (-2, 1),
            (-2, -1), (-1, -2), (1, -2), (2, -1)
        ]
        for dr, dc in directions:
            new_row, new_col = piece.row + dr, piece.col + dc
            if 0 <= new_row < ROWS and 0 <= new_col < COLS:
                target, target_color = self.board[new_row][new_col]
                if target == 1:  # Encountered a blocking box
                    continue
                if target == 0 or (isinstance(target, Piece) and target.color != piece.color and not (piece.color == SPECIAL_RED and target.color == RED) and not (piece.color == SPECIAL_BLUE and target.color == BLUE)):
                    if isinstance(target, Piece) and (target.color == piece.color or (piece.color == SPECIAL_RED and target.color == RED) or (piece.color == SPECIAL_BLUE and target.color == BLUE)):
                        continue  # Skip move if the target is a piece of the same color
                    moves[(new_row, new_col)] = [target] if isinstance(target, Piece) else []

        return moves

    def draw_panel(self, win):
        panel_x = BOARD_WIDTH
        pygame.draw.rect(win, GREY, (panel_x, 0, PANEL_WIDTH, HEIGHT))
        font = pygame.font.SysFont(None, 40)

        turn_text = font.render("Turn:", True, BLACK)
        win.blit(turn_text, (panel_x + 20, 20))

        color_rect = pygame.Rect(panel_x + 20, 70, PANEL_WIDTH - 40, 50)
        pygame.draw.rect(win, self.turn, color_rect)

        red_captures_text = font.render(f"Red Captures: {self.red_captures}", True, BLACK)
        blue_captures_text = font.render(f"Blue Captures: {self.blue_captures}", True, BLACK)
        win.blit(red_captures_text, (panel_x + 20, 140))
        win.blit(blue_captures_text, (panel_x + 20, 200))

        red_points_text = font.render(f"Red Points: {self.red_points}", True, BLACK)
        blue_points_text = font.render(f"Blue Points: {self.blue_points}", True, BLACK)
        win.blit(red_points_text, (panel_x + 20, 260))
        win.blit(blue_points_text, (panel_x + 20, 320))

        if self.setup_phase:
            if self.turn == RED:
                setup_text = font.render("Red, place Blue's knight", True, BLACK)
            else:
                setup_text = font.render("Blue, place Red's knight", True, BLACK)
            win.blit(setup_text, (panel_x + 20, 380))

        # Display remaining time or winner
        if not self.winner:
            elapsed_time = time.time() - self.start_time
            remaining_time = max(0, int(300 - elapsed_time))
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            time_text = font.render(f"Time: {minutes:02}:{seconds:02}", True, BLACK)
            win.blit(time_text, (panel_x + 20, 440))
        else:
            winner_text = font.render(f"{self.winner} Wins!", True, BLACK)
            win.blit(winner_text, (panel_x + 20, 440))

        # Display box button or winner message
        if not self.winner:
            if (self.turn == RED and not any(turns > 0 for _, turns in self.red_boxes)) or (self.turn == BLUE and not any(turns > 0 for _, turns in self.blue_boxes)):
                box_button = pygame.Rect(panel_x + 20, 500, PANEL_WIDTH - 40, 50)
                pygame.draw.rect(win, GREEN, box_button)
                box_text = font.render("Put Box", True, BLACK)
                win.blit(box_text, (panel_x + 40, 510))
                return box_button
        else:
            winner_text = font.render(f"{self.winner} Wins!", True, BLACK)
            win.blit(winner_text, (panel_x + 20, 440))
            reset_button = pygame.Rect(panel_x + 20, 500, PANEL_WIDTH - 40, 50)
            pygame.draw.rect(win, GREEN, reset_button)
            reset_text = font.render("Reset", True, BLACK)
            win.blit(reset_text, (panel_x + 40, 510))
            return reset_button

        return None

    def check_winner(self):
        if self.red_points >= 3:
            self.winner = "Red"
        if self.blue_points >= 3:
            self.winner = "Blue"

        red_pieces = sum(1 for row in self.board for piece, color in row if isinstance(piece, Piece) and (color == RED or color == SPECIAL_RED))
        blue_pieces = sum(1 for row in self.board for piece, color in row if isinstance(piece, Piece) and (color == BLUE or color == SPECIAL_BLUE))

        if red_pieces == 0:
            self.winner = "Blue"
        if blue_pieces == 0:
            self.winner = "Red"

        if red_pieces == 1 and blue_pieces == 1:
            self.winner = "Tie"

        # Check if time has passed
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 300:  # 5 minutes
            if self.red_points > self.blue_points:
                self.winner = "Red"
            elif self.blue_points > self.red_points:
                self.winner = "Blue"
            else:
                if self.red_captures > self.blue_captures:
                    self.winner = "Red"
                elif self.blue_captures > self.red_captures:
                    self.winner = "Blue"
                else:
                    self.winner = "Tie"

        return self.winner

    def reset(self):
        self.__init__()
        self.start_time = time.time()  # Reset the timer



def main():
    run = True
    clock = pygame.time.Clock()
    board = Board()
    action_button = None

    while run:
        clock.tick(60)

        board.check_winner()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if board.winner:
                    if action_button and action_button.collidepoint(pos):
                        board.reset()
                        continue
                elif pos[0] < BOARD_WIDTH:
                    row, col = pos[1] // SQUARE_SIZE, pos[0] // SQUARE_SIZE
                    board.select(row, col)
                elif action_button and action_button.collidepoint(pos) and not board.winner:
                    board.placing_box = True

        board.draw(WIN)
        action_button = board.draw_panel(WIN)
        pygame.display.update()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
