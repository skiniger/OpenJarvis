(* OpenJarvis Launcher — AppleScript-Quelle
   Kompilieren zu .app:
     osacompile -x -o ~/Applications/OpenJarvis.app ~/projects/open-jarvis/scripts/mac_launcher.scpt
   Icon ersetzen:
     1. PNG/ICNS nach OpenJarvis.app/Contents/Resources/applet.icns kopieren
     2. touch OpenJarvis.app (damit LaunchServices refreshed)
*)

on run
	set jarvisPath to "/Users/kinggeorge/projects/open-jarvis"
	set venvActivate to jarvisPath & "/.venv/bin/activate"

	tell application "Terminal"
		if not (exists window 1) then reopen
		set currentTab to selected tab of front window

		-- Wechsle ins Projekt, aktiviere venv, zeige Header
		do script "cd " & quoted form of jarvisPath & " && source " & quoted form of venvActivate & " && clear && echo 'OpenJarvis — Landhaus Bavaria Edition' && echo '' && jarvis agents types 2>/dev/null || true && echo '' && echo 'Bereit. Beispiele:' && echo '  jarvis ask \"Zimmerpreise?\"' && echo '  jarvis ask --agent bavaria_booking \"Neue Buchung\"' && echo '' && zsh -i" in currentTab

		activate
	end tell
end run
