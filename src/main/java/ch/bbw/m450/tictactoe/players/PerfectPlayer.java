package ch.bbw.m450.tictactoe.players;

import java.util.Arrays;
import java.util.Objects;

import ch.bbw.m450.tictactoe.TicTacToeMain;
import ch.bbw.m450.tictactoe.TicTacToePlayer;

/** Vollständige Minimax-Suche; gleiche Bewertungen bevorzugen den kleineren Index. */
public final class PerfectPlayer implements TicTacToePlayer {
    @Override
    public int play(Stone[] board, Stone colorToPlay) {
        Objects.requireNonNull(board, "board");
        Objects.requireNonNull(colorToPlay, "colorToPlay");
        if (board.length != TicTacToeMain.BOARD_SIZE) {
            throw new IllegalArgumentException("A board must contain exactly nine fields");
        }
        if (TicTacToeMain.isWin(board, Stone.CROSS) || TicTacToeMain.isWin(board, Stone.CIRCLE)) {
            throw new IllegalStateException("game is already over");
        }
        var position = Arrays.copyOf(board, board.length);
        var bestMove = -1;
        var bestScore = -11;
        for (var index = 0; index < position.length; index++) {
            if (position[index] == null) {
                position[index] = colorToPlay;
                var score = -evaluate(position, colorToPlay.opponent(), 1);
                position[index] = null;
                if (score > bestScore) {
                    bestScore = score;
                    bestMove = index;
                }
            }
        }
        if (bestMove < 0) {
            throw new IllegalStateException("cannot play at all");
        }
        return bestMove;
    }

    /** Frühe Siege und späte Niederlagen werden bevorzugt; ein Remis zählt null. */
    private int evaluate(Stone[] board, Stone color, int depth) {
        if (TicTacToeMain.isWin(board, color.opponent())) {
            return depth - 10;
        }
        var bestScore = -11;
        for (var index = 0; index < board.length; index++) {
            if (board[index] == null) {
                board[index] = color;
                var score = -evaluate(board, color.opponent(), depth + 1);
                board[index] = null;
                bestScore = Math.max(bestScore, score);
            }
        }
        return bestScore == -11 ? 0 : bestScore;
    }
}
