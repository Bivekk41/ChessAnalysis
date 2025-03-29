import chess.pgn
import chess.engine

# Update the path to point to your actual Stockfish executable
STOCKFISH_PATH = "stockfish/stockfish-windows-x86-64-avx2.exe"
PGN_FILE = "bivek41_vs_meowrrrg_2025.03.27.pgn"  # Make sure to add this file in your root directory

def analyze_game(pgn_path):
    try:
        with open(pgn_path) as pgn:
            game = chess.pgn.read_game(pgn)

        if game is None:
            print("No game found in the PGN file.")
            return

        board = game.board()
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

        prev_score = None
        move_number = 1

        print("Analyzing game...\n")

        for move in game.mainline_moves():
            board.push(move)
            info = engine.analyse(board, chess.engine.Limit(time=0.1))
            score = info["score"].white().score(mate_score=10000)

            if prev_score is not None and score is not None:
                diff = prev_score - score
                if diff >= 300:
                    print(f"Blunder on move {move_number}: {move} (Drop: {diff} cp)")
                elif diff >= 100:
                    print(f"Mistake on move {move_number}: {move} (Drop: {diff} cp)")
                elif diff >= 50:
                    print(f"Inaccuracy on move {move_number}: {move} (Drop: {diff} cp)")

            prev_score = score
            move_number += 1

        engine.quit()
        print("\nAnalysis complete ✅")

    except FileNotFoundError:
        print(f"PGN file '{pgn_path}' not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_game(PGN_FILE)
