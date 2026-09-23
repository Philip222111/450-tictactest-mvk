package ch.bbw.m450.tictactoe;

import java.util.Arrays;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;
import ch.bbw.m450.tictactoe.players.GreedyPlayer;
import ch.bbw.m450.tictactoe.players.HumanPlayer;

/**
 * A small tic-tac-toe board. Initially with a human and a primitive but valid computer player.
 */
public class TicTacToeMain {

	public static final int BOARD_SIZE = 9;

	/** Startet ein Spiel Mensch gegen den einfachen Computergegner. */
	public static void main(String[] args) {
		play(new HumanPlayer(), new GreedyPlayer());
	}

	/**
	 * @param b TicTacToe-board to check for a winner
	 * @param color either X or O
	 * @return true if the colorToPlay wins the current board (has three in a line)
	 */
	public static boolean isWin(Stone[] b, Stone color) {
		// Prüfreihenfolge: drei Zeilen, drei Spalten und zwei Diagonalen.
		// @formatter:off
		return  b[0] == color && b[0] == b[1] && b[1] == b[2] ||
				b[3] == color && b[3] == b[4] && b[4] == b[5] ||
				b[6] == color && b[6] == b[7] && b[7] == b[8] ||
				b[0] == color && b[0] == b[3] && b[3] == b[6] ||
				b[1] == color && b[1] == b[4] && b[4] == b[7] ||
				b[2] == color && b[2] == b[5] && b[5] == b[8] ||
				b[0] == color && b[0] == b[4] && b[4] == b[8] ||
				b[2] == color && b[2] == b[4] && b[4] == b[6];
		// @formatter:on
	}

	/**
	 * Wandelt das eindimensionale Board in eine farbige 3x3-Konsolenausgabe um.
	 * Freie Felder werden mit ihrem spielbaren Index dargestellt.
	 */
	public static String toString(Stone[] board) {
		var sb = new StringBuilder();
		// Die äußere Schleife durchläuft Zeilen, die innere deren drei Spalten.
		for (var i = 0; i < 3; i++) {
			for (var j = 0; j < 3; j++) {
				var index = i * 3 + j;
				// Belegte Felder erscheinen fett, freie Felder grau als Positionsnummer.
				String color = board[index] == Stone.CROSS ? "X" : "O";
				color = "\033[1m" + color + "\033[0m";
				color = board[index] == null ? "\033[37m" + index + "\033[0m" : color;
				sb.append(color)
						.append("  ");
			}
			sb.append("\n");
		}
		return sb.toString();
	}

	/**
	 * The main game loop to play a game of tic-tac-toe with two opponents.
	 *
	 * @param xPlayer the player to start
	 * @param oPlayer the 2nd player. Must not be the same as xPlayer
	 * @return the winning Color or `null` on draw
	 */
	public static Stone play(TicTacToePlayer xPlayer, TicTacToePlayer oPlayer) {
		// Das Board ist ein eindimensionales Array; Index = Zeile * 3 + Spalte.
		//     0 | 1 | 2
		//    ---+---+---
		//     3 | 4 | 5
		//    ---+---+---
		//     6 | 7 | 8
		// Ein Objekt darf nicht gleichzeitig beide Spielerrollen übernehmen.
		if (xPlayer == oPlayer) {
			throw new IllegalArgumentException("players must differ");
		}

		// null kennzeichnet jedes zu Beginn noch freie Feld.
		var board = new Stone[BOARD_SIZE];
		var currentPlayer = xPlayer;
		// Nach höchstens neun gültigen Zügen ist das Board vollständig belegt.
		for (var round = 0; round < BOARD_SIZE; round++) {
			var currentColor = currentPlayer == xPlayer ? Stone.CROSS : Stone.CIRCLE;
			// Eine defensive Kopie verhindert Änderungen am internen Spielzustand.
			var clone = Arrays.copyOf(board, board.length);
			var playTo = currentPlayer.play(clone, currentColor);

			// Nur freie Positionen innerhalb des Boards sind gültige Züge.
			if (playTo < 0 || playTo >= 9 || board[playTo] != null) {
				System.out.println(toString(board));
				throw new IllegalStateException("cannot play to position " + playTo);
			}
			// Der validierte Zug wird in den echten Spielzustand übernommen.
			board[playTo] = currentColor;
			if (isWin(board, currentColor)) {
				System.out.println(toString(board) + "...and the winner is: " + currentColor);
				return currentColor;
			}
			// Ohne Sieg ist im nächsten Durchlauf der andere Spieler an der Reihe.
			currentPlayer = currentPlayer == xPlayer ? oPlayer : xPlayer;
		}

		// Alle neun Züge wurden gespielt, ohne dass eine Gewinnlinie entstand.
		System.out.println("it's a draw!");
		return null;
	}

}
