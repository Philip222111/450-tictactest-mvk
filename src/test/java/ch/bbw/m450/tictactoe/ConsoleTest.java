package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.BoardFixtures.board;
import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CROSS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.NoSuchElementException;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junitpioneer.jupiter.StdIo;
import org.junitpioneer.jupiter.StdOut;

import ch.bbw.m450.tictactoe.players.GreedyPlayer;
import ch.bbw.m450.tictactoe.players.HumanPlayer;

class ConsoleTest {
    @Test
    @StdIo("0")
    void readsFirstPositionAndPrintsPrompt(StdOut out) {
        assertThat(new HumanPlayer().play(board("........."), CROSS)).isZero();
        assertThat(out.capturedString()).contains("Where to put the next CROSS? (0-8):");
    }

    @Test
    @StdIo("8")
    void readsLastPosition() {
        assertThat(new HumanPlayer().play(board("........."), CROSS)).isEqualTo(8);
    }

    @Test
    @StdIo("abc")
    void rejectsNonNumericInput() {
        var player = new HumanPlayer();
        var position = board(".........");
        assertThatThrownBy(() -> player.play(position, CROSS))
                .isInstanceOf(NumberFormatException.class);
    }

    @Test
    @StdIo("")
    void rejectsEndOfInput() throws java.io.IOException {
        System.in.readAllBytes();
        var player = new HumanPlayer();
        var position = board(".........");
        assertThatThrownBy(() -> player.play(position, CROSS))
                .isInstanceOf(NoSuchElementException.class);
    }

    @ParameterizedTest
    @CsvSource({"........., '0 1 2 3 4 5 6 7 8'", "XO......., 'X O 2 3 4 5 6 7 8'"})
    void rendersStonesAndFreePositions(String representation, String expected) {
        var rendered = TicTacToeMain.toString(board(representation))
                .replaceAll("\u001B\\[[;\\d]*m", "");
        assertThat(rendered.trim().split("\\s+")).containsExactly(expected.split(" "));
        assertThat(rendered.lines()).hasSize(3);
    }

    @Test
    @StdIo
    void printsWinner(StdOut out) {
        assertThat(TicTacToeMain.play(new GreedyPlayer(), new GreedyPlayer())).isEqualTo(CROSS);
        assertThat(out.capturedString()).contains("...and the winner is: CROSS");
    }

    @Test
    @StdIo
    void printsDraw(StdOut out) {
        var xMoves = new int[] {0, 2, 3, 7, 8};
        var oMoves = new int[] {1, 4, 5, 6};
        assertThat(TicTacToeMain.play(sequence(xMoves), sequence(oMoves))).isNull();
        assertThat(out.capturedString()).contains("it's a draw!");
    }

    @Test
    @StdIo
    void printsCurrentBoardWhenRejectingAnIllegalMove(StdOut out) {
        var illegalPlayer = sequence(new int[] {-1});
        var opponent = new GreedyPlayer();
        assertThatThrownBy(() -> TicTacToeMain.play(illegalPlayer, opponent))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("cannot play to position -1");
        assertThat(out.capturedString()).contains(TicTacToeMain.toString(board(".........")));
    }

    private static TicTacToePlayer sequence(int[] moves) {
        return new TicTacToePlayer() {
            private int next;

            @Override
            public int play(Stone[] position, Stone color) {
                return moves[next++];
            }
        };
    }
}
