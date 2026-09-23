package ch.bbw.m450.tictactoe.players;

import java.nio.charset.StandardCharsets;
import java.util.Scanner;

import ch.bbw.m450.tictactoe.TicTacToeMain;
import ch.bbw.m450.tictactoe.TicTacToePlayer;

/**
 * Simple human-player taking input from stdin.
 */
public class HumanPlayer implements TicTacToePlayer {

	@Override
	public int play(Stone[] board, Stone colorToPlay) {
		// Zeigt den aktuellen Stand und liest genau eine Positionsnummer ein.
		System.out.println(TicTacToeMain.toString(board) + "Where to put the next " + colorToPlay + "? (0-8): ");
		var scanner = new Scanner(System.in, StandardCharsets.UTF_8);
		return Integer.parseInt(scanner.nextLine());
	}
}
