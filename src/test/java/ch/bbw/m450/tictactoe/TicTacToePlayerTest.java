package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.BoardFixtures.board;
import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CIRCLE;
import static ch.bbw.m450.tictactoe.TicTacToePlayer.Stone.CROSS;

import org.assertj.core.api.WithAssertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import ch.bbw.m450.tictactoe.players.GreedyPlayer;

class TicTacToePlayerTest implements WithAssertions {

    // Der zustandslose GreedyPlayer kann für alle Testfälle wiederverwendet werden.
    private final GreedyPlayer greedyPlayer = new GreedyPlayer();

    @ParameterizedTest(name = "{0} -> first free field {1}")
    @CsvSource({
            "........., 0",
            "XO......., 2",
            "XOXOXOXO., 8"
    })
    void greedyPlayerChoosesTheFirstFreeField(String representation, int expectedPosition) {
        // Jeder CSV-Datensatz prüft eine andere Position des ersten freien Felds.
        assertThat(greedyPlayer.play(board(representation), CROSS)).isEqualTo(expectedPosition);
    }

    @Test
    void greedyPlayerRejectsAFullBoard() {
        // Ohne freies Feld muss der Spieler den unmöglichen Zug ausdrücklich melden.
        assertThatIllegalStateException()
                .isThrownBy(() -> greedyPlayer.play(board("XOXOOXXXO"), CIRCLE))
                .withMessage("cannot play at all");
    }

    @Test
    void stonesReturnTheirOpponent() {
        // Die Gegenrichtung wird mitgeprüft, damit die Zuordnung symmetrisch bleibt.
        assertThat(CROSS.opponent()).isEqualTo(CIRCLE);
        assertThat(CIRCLE.opponent()).isEqualTo(CROSS);
    }

}
