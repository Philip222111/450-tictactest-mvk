# Nachweise zu den Detailaufträgen

Stand: 4. November 2026. Dieses Dokument wird nach den tatsächlichen Läufen
ergänzt. Die erste Cloud-Iteration ist in `CLOUD_NACHWEIS.md` historisch dokumentiert.

- Bestehende EC2 `i-0e9c89d71a5e61c34` beibehalten; keine Ersetzung.
- Elastic IP `98.87.74.14`, ttyd 1.7.7, nginx und LabInstanceProfile eingerichtet.
- Konsole: <http://ec2-98-87-74-14.compute-1.amazonaws.com/terminal/>.
- Echter PTY-/WebSocket-Test mit einer vollständigen Partie erfolgreich.
- Laufzeitinstallation über die SSM-Association erfolgreich.
- Lab-Sperre auf S3 Object Lock beobachtet und durch dokumentierten
  separaten Bucket-Bootstrap berücksichtigt, ohne zusätzliche IAM-Rechte.

## Noch zu protokollierende Versuche

Release A/B manuell, Frontend-only, Backend-only, beide, reine Dokumentation,
Rollback, Fehlerfall, Credential-Fehler und Stop/Start werden nach Durchführung
mit tatsächlichen Ergebnissen und Workflow-Links eingetragen.

Ein tatsächlicher Wechsel der Learner-Lab-Sitzung sowie ein vollständiges
`destroy`/Neuaufbau der laufenden Instanz werden nicht als ausgeführt behauptet.
Die Schritte und Auswirkungen sind in deployment.md beschrieben.
