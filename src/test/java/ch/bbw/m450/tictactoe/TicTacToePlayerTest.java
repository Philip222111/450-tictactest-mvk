package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CIRCLE;
import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CROSS;

import org.assertj.core.api.WithAssertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;
import ch.bbw.m450.tictactoe.players.GreedyPlayer;

class TicTacToePlayerTest implements WithAssertions {

    private final GreedyPlayer greedyPlayer = new GreedyPlayer();

    @ParameterizedTest(name = "{0} -> first free field {1}")
    @CsvSource({
            "........., 0",
            "XO......., 2",
            "XOXOXOXO., 8"
    })
    void greedyPlayerChoosesTheFirstFreeField(String representation, int expectedPosition) {
        assertThat(greedyPlayer.play(board(representation), CROSS)).isEqualTo(expectedPosition);
    }

    @Test
    void greedyPlayerRejectsAFullBoard() {
        assertThatIllegalStateException()
                .isThrownBy(() -> greedyPlayer.play(board("XOXOOXXXO"), CIRCLE))
                .withMessage("cannot play at all");
    }

    @Test
    void stonesReturnTheirOpponent() {
        assertThat(CROSS.opponent()).isEqualTo(CIRCLE);
        assertThat(CIRCLE.opponent()).isEqualTo(CROSS);
    }

    private static Stone[] board(String representation) {
        var board = new Stone[TicTacToeMain.BOARD_SIZE];
        for (var i = 0; i < representation.length(); i++) {
            board[i] = switch (representation.charAt(i)) {
                case 'X' -> CROSS;
                case 'O' -> CIRCLE;
                case '.' -> null;
                default -> throw new IllegalArgumentException("Unknown board character");
            };
        }
        return board;
    }
}
