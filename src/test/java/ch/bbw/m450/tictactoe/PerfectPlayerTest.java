package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.BoardFixtures.board;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.EnumSource;
import org.junitpioneer.jupiter.StdIo;
import org.junitpioneer.jupiter.StdOut;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;
import ch.bbw.m450.tictactoe.players.PerfectPlayer;

class PerfectPlayerTest {
    private final PerfectPlayer player = new PerfectPlayer();

    @ParameterizedTest
    @CsvSource({
        "XX.OO...., CROSS, 2",
        "XX.OO.X.., CIRCLE, 5",
        "XX..O...., CIRCLE, 2",
        "OO..X...X, CROSS, 2",
        "XOXOXOOX., CROSS, 8"
    })
    void winsBlocksOrCompletesADraw(String representation, Stone color, int expected) {
        var position = board(representation);
        var original = position.clone();
        assertThat(player.play(position, color)).isEqualTo(expected);
        assertThat(position).containsExactly(original);
    }

    @Test
    void choosesLowestIndexWhenSeveralMovesHaveTheSameValue() {
        assertThat(player.play(board("........."), Stone.CROSS)).isZero();
    }

    @ParameterizedTest
    @EnumSource(Stone.class)
    void neverLosesAgainstAnyLegalOpponentContinuation(Stone ownColor) {
        // Nur die deterministische Zugberechnung wird gecacht; alle gegnerischen
        // Zugfolgen werden bis zum Spielende tatsächlich durchlaufen.
        var leaves = explore(new Stone[9], Stone.CROSS, ownColor, new HashMap<>());
        assertThat(leaves).as("terminal opponent continuations").isPositive();
    }

    private int explore(Stone[] position, Stone turn, Stone ownColor, Map<String, Integer> moves) {
        assertThat(TicTacToeMain.isWin(position, ownColor.opponent()))
                .as("no defeat for %s on %s", ownColor, Arrays.toString(position)).isFalse();
        if (TicTacToeMain.isWin(position, ownColor) || Arrays.stream(position).noneMatch(s -> s == null)) {
            return 1;
        }
        if (turn == ownColor) {
            var snapshot = position.clone();
            var move = moves.computeIfAbsent(Arrays.toString(position), key -> player.play(position, turn));
            assertThat(position).containsExactly(snapshot);
            assertThat(move).isBetween(0, 8);
            assertThat(position[move]).isNull();
            position[move] = turn;
            var leaves = explore(position, turn.opponent(), ownColor, moves);
            position[move] = null;
            return leaves;
        }
        var leaves = 0;
        for (var index = 0; index < position.length; index++) {
            if (position[index] == null) {
                position[index] = turn;
                leaves += explore(position, turn.opponent(), ownColor, moves);
                position[index] = null;
            }
        }
        return leaves;
    }

    @Test
    @StdIo
    void integratesWithGameAndDrawsAgainstItself(StdOut out) {
        assertThat(TicTacToeMain.play(player, new PerfectPlayer())).isNull();
        assertThat(out.capturedString()).contains("it's a draw!");
    }

    @ParameterizedTest
    @CsvSource({"XXXOO...., CROSS", "XX.OOOX.., CIRCLE", "XOXOOXXXO, CROSS"})
    void rejectsFinishedGames(String representation, Stone color) {
        assertThatThrownBy(() -> player.play(board(representation), color))
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void rejectsMalformedArguments() {
        assertThatThrownBy(() -> player.play(null, Stone.CROSS)).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> player.play(new Stone[9], null)).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> player.play(new Stone[8], Stone.CROSS))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
