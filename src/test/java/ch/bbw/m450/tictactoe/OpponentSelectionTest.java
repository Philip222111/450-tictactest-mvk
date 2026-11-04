package ch.bbw.m450.tictactoe;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.junitpioneer.jupiter.StdIo;
import org.junitpioneer.jupiter.StdOut;

class OpponentSelectionTest {
    @Test
    @StdIo({"1", "0", "4", "8"})
    void humanCanBeatSelectedGreedyPlayer(StdOut out) {
        TicTacToeMain.main(new String[0]);
        assertThat(out.capturedString()).contains("gegen GreedyPlayer", "winner is: CROSS")
                .doesNotContain("Bitte 1 fuer Greedy");
    }

    @Test
    @StdIo({"2", "0", "1", "3"})
    void selectedPerfectPlayerPunishesLosingMoves(StdOut out) {
        TicTacToeMain.main(new String[0]);
        assertThat(out.capturedString()).contains("gegen PerfectPlayer", "winner is: CIRCLE")
                .doesNotContain("winner is: CROSS");
    }

    @Test
    @StdIo({"invalid", "1", "0", "4", "8"})
    void invalidSelectionIsRetriedWithoutLosingGameInput(StdOut out) {
        TicTacToeMain.main(new String[0]);
        assertThat(out.capturedString()).contains("Bitte 1 fuer Greedy", "winner is: CROSS");
    }

    @Test
    @StdIo("")
    void closedInputDoesNotStartAGame(StdOut out) throws java.io.IOException {
        System.in.readAllBytes();
        TicTacToeMain.main(new String[0]);
        assertThat(out.capturedString()).contains("Gegner (1=Greedy, 2=Perfect):")
                .doesNotContain("Where to put", "winner is:");
    }
}
