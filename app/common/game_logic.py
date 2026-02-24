
"""
    Tablero de 6 filas x 7 columnas:
    - 0 = casilla vacía
    - 1 = ficha del jugador 1
    - 2 = ficha del jugador 2
"""

class Board:

    
    def __init__(self):
        self.rows = 6
        self.cols = 7
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
    
    
    def drop_piece(self, column, player):
        if column < 0 or column >= self.cols:
            return False, None
        
        for row in range(self.rows - 1, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = player
                return True, row
        
        return False, None
    
    
    def is_column_full(self, column):
        if column < 0 or column >= self.cols:
            return True
        
        return self.board[0][column] != 0
    
    
    def check_winner(self):
        
        # Verificar horizontal
        for row in range(self.rows):
            for col in range(self.cols - 3):
                if self.board[row][col] != 0:
                    if (self.board[row][col] == self.board[row][col + 1] ==
                        self.board[row][col + 2] == self.board[row][col + 3]):
                        return self.board[row][col]
        
        # Verificar vertical 
        for row in range(self.rows - 3):
            for col in range(self.cols):
                if self.board[row][col] != 0:
                    if (self.board[row][col] == self.board[row + 1][col] ==
                        self.board[row + 2][col] == self.board[row + 3][col]):
                        return self.board[row][col]
        
        # Verificar diagonal 1
        for row in range(3, self.rows):
            for col in range(self.cols - 3):
                if self.board[row][col] != 0:
                    if (self.board[row][col] == self.board[row - 1][col + 1] ==
                        self.board[row - 2][col + 2] == self.board[row - 3][col + 3]):
                        return self.board[row][col]
        
        # Verificar diagonal 2
        for row in range(self.rows - 3):
            for col in range(self.cols - 3):
                if self.board[row][col] != 0:
                    if (self.board[row][col] == self.board[row + 1][col + 1] ==
                        self.board[row + 2][col + 2] == self.board[row + 3][col + 3]):
                        return self.board[row][col]
        return 0
    
    
    def is_board_full(self):
        for col in range(self.cols):
            if self.board[0][col] == 0:
                return False
        return True
    
    
    def get_board_state(self):
        return [row[:] for row in self.board]
    
    
    def __str__(self):

        symbols = {0: '·', 1: '●', 2: '○'}
        
        lines = []
        lines.append("   1 2 3 4 5 6 7")  # Números de columnas
        lines.append(" ┌───────────────┐")
        
        for row in self.board:
            line = " │ " + " ".join(symbols[cell] for cell in row) + " │"
            lines.append(line)
        
        lines.append(" └───────────────┘")
        
        return "\n".join(lines)


def test():
    print("=== Test de Board ===\n")
    
    board = Board()
    print("Tablero inicial:")
    print(board)
    print()
    
    # Jugador 1 coloca en columna 3
    success, row = board.drop_piece(3, 1)
    print(f"Jugador 1 coloca en columna 4 (índice 3): {success}, cayó en fila {row}")
    print(board)
    print()
    
    # Jugador 2 coloca en columna 3
    success, row = board.drop_piece(3, 2)
    print(f"Jugador 2 coloca en columna 4 (índice 3): {success}, cayó en fila {row}")
    print(board)
    print()
    
    # Jugador 1 coloca en columna 4
    board.drop_piece(4, 1)
    # Jugador 2 coloca en columna 4
    board.drop_piece(4, 2)
    print("Después de más jugadas:")
    print(board)
    print()
    
    
    # Probar victoria horizontal
    board2 = Board()
    for i in range(4):
        board2.drop_piece(i, 1)
    print("Tablero con 4 en línea horizontal:")
    print(board2)
    winner = board2.check_winner()
    print(f"Ganador: {winner}")
    print()
    
    
if __name__ == "__main__":

    test()