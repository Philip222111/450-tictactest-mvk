package ch.bbw.m450.tictactoe;

import ch.bbw.m450.tictactoe.TicTacToePlayer.Stone;

/** Gemeinsame, kompakte Darstellung von Teststellungen. */
final class BoardFixtures {
    private BoardFixtures() {
    }

    static Stone[] board(String representation) {
        var fields = representation.replace(" ", "");
        if (fields.length() != TicTacToeMain.BOARD_SIZE) {
            throw new IllegalArgumentException("A board must contain exactly nine fields");
        }
        var result = new Stone[fields.length()];
        for (var index = 0; index < fields.length(); index++) {
            result[index] = switch (fields.charAt(index)) {
                case 'X' -> Stone.CROSS;
                case 'O' -> Stone.CIRCLE;
                case '.' -> null;
                default -> throw new IllegalArgumentException("Unknown board character: " + fields.charAt(index));
            };
        }
        return result;
    }
}
