package ch.bbw.m450.tictactoe.players;

import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Scanner;

import ch.bbw.m450.tictactoe.TicTacToeMain;
import ch.bbw.m450.tictactoe.TicTacToePlayer;

/**
 * Simple human-player taking input from stdin.
 */
// The board and prompt are console UI, not diagnostic logging.
@SuppressWarnings("java:S106")
public class HumanPlayer implements TicTacToePlayer {
    private final Scanner scanner;

    public HumanPlayer() {
        this(new Scanner(System.in, StandardCharsets.UTF_8));
    }

    /** Teilt die Eingabe mit der Gegnerauswahl, ohne gepufferte Zeilen zu verlieren. */
    public HumanPlayer(Scanner scanner) {
        this.scanner = Objects.requireNonNull(scanner, "scanner");
    }

    @Override
    public int play(Stone[] board, Stone colorToPlay) {
        // Zeigt den aktuellen Stand und liest genau eine Positionsnummer ein.
        System.out.println(TicTacToeMain.toString(board) + "Where to put the next " + colorToPlay + "? (0-8): ");
        return Integer.parseInt(scanner.nextLine());
    }
}
