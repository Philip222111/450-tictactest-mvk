package ch.bbw.m450.tictactoe;

import static ch.bbw.m450.tictactoe.TicTacToeMain.isWin;

import org.assertj.core.api.WithAssertions;
import org.junit.jupiter.api.Test;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;

class TicTacToeMainTest implements WithAssertions {

    @Test
    void dummyTest() {
        assertThat(false).isFalse();
    }

    @Test
void isWinningDiagonalForX() {
    assertThat(isWin(toBoard("XOO OX. XOX"), Stone.CROSS)).isTrue();
}

@Test
void isNotWinningForO() {
    assertThat(isWin(toBoard("XOO OX. XOX"), Stone.CIRCLE)).isFalse();
}

    @Test
    void isWinningHorizontalForX() {
        assertThat(isWin(toBoard("XXX OO. ..."), Stone.CROSS)).isTrue();
    }

    @Test
    void isWinningVerticalForO() {
        assertThat(isWin(toBoard("OX. OX. O.."), Stone.CIRCLE)).isTrue();
    }

    @Test
    void noWinnerOnEmptyBoard() {
        assertThat(isWin(toBoard("... ... ..."), Stone.CROSS)).isFalse();
    }

    private Stone[] toBoard(String board) {
        var result = new Stone[9];
        var cleanedBoard = board.replace(" ", "");

        for (var i = 0; i < cleanedBoard.length(); i++) {
            result[i] = switch (cleanedBoard.charAt(i)) {
                case 'X' -> Stone.CROSS;
                case 'O' -> Stone.CIRCLE;
                case '.' -> null;
                default -> throw new IllegalArgumentException(
                        "Unknown character: " + cleanedBoard.charAt(i)
                );
            };
        }

        return result;
    }
}