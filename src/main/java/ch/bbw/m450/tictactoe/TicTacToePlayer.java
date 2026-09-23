package ch.bbw.m450.tictactoe;

public interface TicTacToePlayer {

	/**
	 * Bestimmt den nächsten Zug auf einem teilweise belegten Spielfeld.
	 *
	 * @param board aktuelle, defensive Kopie des Spielfelds
	 * @param colorToPlay eigener Spielstein
	 * @return gewählte Position von 0 bis 8; 0 ist links oben
	 */
	int play(Stone[] board, Stone colorToPlay);

	/**
	 * Repräsentiert die beiden möglichen Zustände eines belegten Felds.
	 */
	enum Stone {
		CROSS, CIRCLE;

		public Stone opponent() {
			// Für zwei mögliche Steine genügt die direkte Umschaltung.
			return this == Stone.CROSS ? Stone.CIRCLE : Stone.CROSS;
		}
	}
}
