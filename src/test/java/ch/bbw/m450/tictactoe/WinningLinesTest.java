package ch.bbw.m450.tictactoe;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Arrays;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;

class WinningLinesTest {
    private static final int[][] LINES = {
        {0, 1, 2}, {3, 4, 5}, {6, 7, 8}, {0, 3, 6},
        {1, 4, 7}, {2, 5, 8}, {0, 4, 8}, {2, 4, 6}
    };

    @ParameterizedTest(name = "{0}, line {1}")
    @MethodSource("winningLines")
    void recognizesEveryLineForBothColors(Stone color, int lineIndex) {
        var board = new Stone[TicTacToeMain.BOARD_SIZE];
        for (var index : LINES[lineIndex]) {
            board[index] = color;
        }
        assertThat(TicTacToeMain.isWin(board, color)).as("completed line %s", lineIndex).isTrue();
        assertThat(TicTacToeMain.isWin(board, color.opponent())).as("opponent has no line").isFalse();
    }

    @ParameterizedTest(name = "{0}, line {1}, missing field {2}")
    @MethodSource("incompleteLines")
    void rejectsEveryInterruptedLine(Stone color, int lineIndex, int missing) {
        var board = new Stone[TicTacToeMain.BOARD_SIZE];
        for (var index : LINES[lineIndex]) {
            board[index] = color;
        }
        board[LINES[lineIndex][missing]] = color.opponent();
        assertThat(TicTacToeMain.isWin(board, color)).as("interrupted line %s", lineIndex).isFalse();
    }

    private static Stream<Arguments> winningLines() {
        return Arrays.stream(Stone.values()).flatMap(color ->
                IntStream.range(0, LINES.length).mapToObj(line -> Arguments.of(color, line)));
    }

    private static Stream<Arguments> incompleteLines() {
        return Arrays.stream(Stone.values()).flatMap(color -> IntStream.range(0, LINES.length)
                .boxed().flatMap(line -> IntStream.range(0, 3)
                        .mapToObj(missing -> Arguments.of(color, line, missing))));
    }
}
