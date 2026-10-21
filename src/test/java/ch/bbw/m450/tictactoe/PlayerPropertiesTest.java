package ch.bbw.m450.tictactoe;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;
import ch.bbw.m450.tictactoe.players.GreedyPlayer;
import ch.bbw.m450.tictactoe.players.PerfectPlayer;
import net.jqwik.api.Arbitraries;
import net.jqwik.api.Arbitrary;
import net.jqwik.api.ForAll;
import net.jqwik.api.Property;
import net.jqwik.api.Provide;

class PlayerPropertiesTest {
    @Property(tries = 150, seed = "4502026")
    void playersChooseFreeFieldsWithoutChangingLegalBoards(@ForAll("moveOrders") List<Integer> order) {
        var board = new Stone[9];
        var turn = Stone.CROSS;
        for (var move : order) {
            for (var player : List.of(new GreedyPlayer(), new PerfectPlayer())) {
                var snapshot = board.clone();
                var selected = player.play(board, turn);
                assertThat(selected).isBetween(0, 8);
                assertThat(board[selected]).isNull();
                assertThat(board).containsExactly(snapshot);
            }
            board[move] = turn;
            if (TicTacToeMain.isWin(board, turn)) {
                break;
            }
            turn = turn.opponent();
        }
    }

    @Provide
    Arbitrary<List<Integer>> moveOrders() {
        return Arbitraries.integers().between(0, 8).list().uniqueElements().ofSize(9);
    }
}
