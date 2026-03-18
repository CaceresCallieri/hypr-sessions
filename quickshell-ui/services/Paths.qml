pragma Singleton

import Quickshell

Singleton {
    readonly property string home: Quickshell.env("HOME")
    readonly property string cli: home + "/projects/hypr-sessions/hypr-sessions.py" // dev-only; update if project moves

    function shortenHome(path: string): string {
        if (path === home)
            return "~";
        if (path.startsWith(home + "/"))
            return "~" + path.slice(home.length);
        return path;
    }
}
