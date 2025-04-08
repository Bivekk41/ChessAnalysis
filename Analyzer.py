import chess.pgn
import chess.engine
import sys
import tkinter as tk
from PIL import Image, ImageTk
import os
import time

# === CONFIGURATION ===
STOCKFISH_PATH = "stockfish/stockfish-windows-x86-64-avx2.exe"
ANALYSIS_TIME = 0.3
DELAY_BETWEEN_MOVES = .5  # seconds
THRESHOLD_BLUNDER = 300
THRESHOLD_MISTAKE = 100
THRESHOLD_INACCURACY = 50
PIECE_FOLDER = "pieces"
SQUARE_SIZE = 64
BOARD_SIZE = SQUARE_SIZE * 8
MESSAGE_HEIGHT = 38

# === GUI CLASS ===
class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=BOARD_SIZE, height=BOARD_SIZE + MESSAGE_HEIGHT)
        self.canvas.pack()
        self.square_colors = [(238, 238, 210), (118, 150, 86)]
        self.piece_images = self.load_piece_images()
        self.message = ""
        self.arrow = None

    def load_piece_images(self):
        images = {}
        piece_map = {
            "P": "pawn.jpg", "N": "knight.jpg", "B": "bishop.jpg", "R": "rook.jpg",
            "Q": "queen.png", "K": "king.jpg",
            "p": "pawn_black.png", "n": "knight_black.jpg", "b": "bishop_black.png",
            "r": "rook_black.png", "q": "black_queen.png", "k": "king_black.jpg"
        }
        for symbol, file in piece_map.items():
            path = os.path.join(PIECE_FOLDER, file)
            if os.path.exists(path):
                img = Image.open(path).resize((SQUARE_SIZE, SQUARE_SIZE))
                images[symbol] = ImageTk.PhotoImage(img)
        return images

    def draw_board(self, board, best_move=None):
        self.canvas.delete("all")
        # Draw squares
        for row in range(8):
            for col in range(8):
                color = self.square_colors[(row + col) % 2]
                x0 = col * SQUARE_SIZE
                y0 = row * SQUARE_SIZE
                x1 = x0 + SQUARE_SIZE
                y1 = y0 + SQUARE_SIZE
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=self._rgb(color), outline="")

        # Draw pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                symbol = piece.symbol()
                img = self.piece_images.get(symbol)
                if img:
                    col = chess.square_file(square)
                    row = 7 - chess.square_rank(square)
                    x = col * SQUARE_SIZE
                    y = row * SQUARE_SIZE
                    self.canvas.create_image(x, y, anchor='nw', image=img)

        # Draw best move arrow if provided
        if best_move:
            from_sq = best_move.from_square
            to_sq = best_move.to_square
            fx, fy = chess.square_file(from_sq), 7 - chess.square_rank(from_sq)
            tx, ty = chess.square_file(to_sq), 7 - chess.square_rank(to_sq)
            self.canvas.create_line(
                fx * SQUARE_SIZE + SQUARE_SIZE // 2, fy * SQUARE_SIZE + SQUARE_SIZE // 2,
                tx * SQUARE_SIZE + SQUARE_SIZE // 2, ty * SQUARE_SIZE + SQUARE_SIZE // 2,
                fill="red", width=3, arrow=tk.LAST
            )

        # Draw message
        if self.message:
            self.canvas.create_rectangle(0, BOARD_SIZE, BOARD_SIZE, BOARD_SIZE + MESSAGE_HEIGHT, fill="white", outline="")
            self.canvas.create_text(BOARD_SIZE // 2, BOARD_SIZE + MESSAGE_HEIGHT // 2,
                                    text=self.message, font=("Arial", 16, "bold"), fill="red")

        self.root.update()

    def _rgb(self, rgb_tuple):
        return "#%02x%02x%02x" % rgb_tuple

# === ANALYSIS LOGIC ===
def analyze_game(pgn_path):
    try:
        with open(pgn_path) as pgn:
            game = chess.pgn.read_game(pgn)

        if not game:
            print("No game found in the PGN file.")
            return

        board = game.board()
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

        print("\n🔍 Starting real-time analysis...\n")

        root = tk.Tk()
        root.title("Chess Analyzer")
        gui = ChessGUI(root)
        gui.draw_board(board)

        prev_score = None
        move_number = 1

        for move in game.mainline_moves():
            player = "White" if board.turn else "Black"
            # Get best move before making the actual move
            best_info = engine.analyse(board, chess.engine.Limit(time=ANALYSIS_TIME))
            best_move = best_info.get("pv", [None])[0]

            board.push(move)
            played_info = engine.analyse(board, chess.engine.Limit(time=ANALYSIS_TIME))
            score = played_info["score"].white().score(mate_score=10000)

            prefix = f"{move_number}. " if player == "White" else f"{move_number}... "
            print(f"{prefix}{move} — {player} to move — Score: {score / 100.0:.2f} cp")

            gui.message = ""
            arrow = None

            if prev_score is not None and score is not None:
                drop = prev_score - score
                if drop >= THRESHOLD_BLUNDER:
                    gui.message = f"⛔ {player} blundered!"
                    arrow = best_move
                    print(f"  {gui.message} (Drop: {drop} cp)")
                elif drop >= THRESHOLD_MISTAKE:
                    gui.message = f"⚠️ {player} made a mistake!"
                    arrow = best_move
                    print(f"  {gui.message} (Drop: {drop} cp)")
                elif drop >= THRESHOLD_INACCURACY:
                    gui.message = f"❗ {player} was inaccurate!"
                    arrow = best_move
                    print(f"  {gui.message} (Drop: {drop} cp)")

            prev_score = score
            gui.draw_board(board, best_move if gui.message else None)
            time.sleep(DELAY_BETWEEN_MOVES)

            if player == "Black":
                move_number += 1

        engine.quit()
        print("\n✅ Real-time analysis complete.")
        root.mainloop()

    except FileNotFoundError:
        print(f"❌ PGN file not found: {pgn_path}")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

# === ENTRY POINT ===
if __name__ == "__main__":
    if len(sys.argv) > 1:
        PGN_FILE = sys.argv[1].replace("\\", "/")
        print(f"📂 Using custom PGN file: {PGN_FILE}")
    else:
        PGN_FILE = "bivek41_vs_meowrrrg_2025.03.27.pgn"
        print(f"📂 No custom PGN specified. Using default: {PGN_FILE}")

    analyze_game(PGN_FILE)
