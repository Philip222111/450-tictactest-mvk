package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.TicTacToeMain.play;
import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CIRCLE;
import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CROSS;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.assertj.core.api.WithAssertions;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;

class TicTacToeGameTest implements WithAssertions {

    private PrintStream originalOut;
    private ByteArrayOutputStream output;

    @BeforeEach
    void captureConsoleOutput() {
        originalOut = System.out;
        output = new ByteArrayOutputStream();
        System.setOut(new PrintStream(output, true, StandardCharsets.UTF_8));
    }

    @AfterEach
    void restoreConsoleOutput() {
        System.setOut(originalOut);
    }

    @Test
    void playsAlternatingTurnsUntilCrossWins() {
        var xPlayer = new ScriptedPlayer(0, 1, 2);
        var oPlayer = new ScriptedPlayer(3, 4);

        assertThat(play(xPlayer, oPlayer)).isEqualTo(CROSS);
        assertThat(xPlayer.colors).containsExactly(CROSS, CROSS, CROSS);
        assertThat(oPlayer.colors).containsExactly(CIRCLE, CIRCLE);
        assertThat(xPlayer.boards.get(1)).containsExactly(
                CROSS, null, null,
                CIRCLE, null, null,
                null, null, null);
        assertThat(output.toString(StandardCharsets.UTF_8)).contains("the winner is: CROSS");
    }

    @Test
    void circleCanWinAfterCrossStarts() {
        assertThat(play(
                new ScriptedPlayer(0, 1, 8),
                new ScriptedPlayer(3, 4, 5)))
                .isEqualTo(CIRCLE);
    }

    @Test
    void nineValidMovesWithoutWinningLineAreADraw() {
        assertThat(play(
                new ScriptedPlayer(0, 2, 3, 7, 8),
                new ScriptedPlayer(1, 4, 5, 6)))
                .isNull();
        assertThat(output.toString(StandardCharsets.UTF_8)).contains("it's a draw!");
    }

    @ParameterizedTest(name = "position {0} is outside the board")
    @ValueSource(ints = {-1, TicTacToeMain.BOARD_SIZE})
    void rejectsMovesOutsideTheBoard(int position) {
        assertThatThrownBy(() -> play(new ScriptedPlayer(position), new ScriptedPlayer(0)))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("cannot play to position " + position);
    }

    @Test
    void rejectsMovesToAnOccupiedField() {
        assertThatThrownBy(() -> play(new ScriptedPlayer(0), new ScriptedPlayer(0)))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("cannot play to position 0");
    }

    @Test
    void rejectsTheSamePlayerInstanceForBothColors() {
        var player = new ScriptedPlayer(0);

        assertThatIllegalArgumentException()
                .isThrownBy(() -> play(player, player))
                .withMessage("players must differ");
    }

    @Test
    void playersReceiveDefensiveBoardCopies() {
        assertThat(play(
                new ScriptedPlayer(true, 0, 2, 3, 7, 8),
                new ScriptedPlayer(true, 1, 4, 5, 6)))
                .isNull();
    }

    private static final class ScriptedPlayer implements TicTacToePlayer {
        private final boolean mutateReceivedBoard;
        private final int[] moves;
        private final List<Stone> colors = new ArrayList<>();
        private final List<Stone[]> boards = new ArrayList<>();
        private int nextMove;

        private ScriptedPlayer(int... moves) {
            this(false, moves);
        }

        private ScriptedPlayer(boolean mutateReceivedBoard, int... moves) {
            this.mutateReceivedBoard = mutateReceivedBoard;
            this.moves = moves;
        }

        @Override
        public int play(Stone[] board, Stone colorToPlay) {
            colors.add(colorToPlay);
            boards.add(Arrays.copyOf(board, board.length));
            if (mutateReceivedBoard) {
                Arrays.fill(board, colorToPlay);
            }
            return moves[nextMove++];
        }
    }
}
