package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.TicTacToeMain.isWin;

import java.util.stream.Stream;

import org.assertj.core.api.WithAssertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;

class TicTacToeMainTest implements WithAssertions {

    // Testdaten
    private Stone[] emptyBoard;

    // Vorbereitung
    @BeforeEach
    void setUp() {
        emptyBoard = board("... ... ...");
    }

    // Gewinnvarianten
    @ParameterizedTest(name = "{0}")
    @MethodSource("winningBoards")
    void detectsWinningBoards(String description, String representation, Stone winner) {
        assertWinner(board(representation), winner);
    }

    // Leeres Spielfeld
    @Test
    void noWinnerOnEmptyBoard() {
        assertNoWinner(emptyBoard, Stone.CROSS);
        assertNoWinner(emptyBoard, Stone.CIRCLE);
    }

    // Gegenprobe
    @ParameterizedTest(name = "{0}")
    @MethodSource("nonWinningBoards")
    void rejectsBoardsWithoutWinner(String description, String representation, Stone stone) {
        assertNoWinner(board(representation), stone);
    }

    // Testfälle
    private static Stream<Arguments> winningBoards() {
        return Stream.of(
                Arguments.of("X gewinnt oben", "XXX OO. ...", Stone.CROSS),
                Arguments.of("O gewinnt mittig", "XX. OOO X..", Stone.CIRCLE),
                Arguments.of("X gewinnt unten", "OO. ... XXX", Stone.CROSS),
                Arguments.of("O gewinnt links", "OX. OX. O..", Stone.CIRCLE),
                Arguments.of("X gewinnt mittig vertikal", "OXO .X. OX.", Stone.CROSS),
                Arguments.of("O gewinnt rechts", "XXO X.O ..O", Stone.CIRCLE),
                Arguments.of("X gewinnt diagonal", "XOO OX. ..X", Stone.CROSS),
                Arguments.of("O gewinnt gegendiagonal", "XXO XO. O..", Stone.CIRCLE)
        );
    }

    private static Stream<Arguments> nonWinningBoards() {
        return Stream.of(
                Arguments.of("X hat nur zwei Steine", "XX. OO. ...", Stone.CROSS),
                Arguments.of("O hat nur zwei Steine", "XO. XO. ...", Stone.CIRCLE),
                Arguments.of("Volles Board ohne O-Sieg", "XOX XXO OXO", Stone.CIRCLE)
        );
    }

    // Siegerprüfung
    private void assertWinner(Stone[] board, Stone stone) {
        assertThat(isWin(board, stone)).isTrue();
    }

    // Verliererprüfung
    private void assertNoWinner(Stone[] board, Stone stone) {
        assertThat(isWin(board, stone)).isFalse();
    }

    // Spielfeldumwandlung
    private Stone[] board(String representation) {
        var cleanedBoard = representation.replace(" ", "");
        assertThat(cleanedBoard)
                .as("A board must contain exactly nine fields")
                .hasSize(TicTacToeMain.BOARD_SIZE);

        var result = new Stone[TicTacToeMain.BOARD_SIZE];

        for (var i = 0; i < cleanedBoard.length(); i++) {
            result[i] = switch (cleanedBoard.charAt(i)) {
                case 'X' -> Stone.CROSS;
                case 'O' -> Stone.CIRCLE;
                case '.' -> null;
                default -> throw new IllegalArgumentException(
                        "Unknown board character: " + cleanedBoard.charAt(i)
                );
            };
        }

        return result;
    }
}
