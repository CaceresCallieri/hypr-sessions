//@ pragma Env QT_QPA_PLATFORM=wayland
//@ pragma Env QSG_RENDER_LOOP=threaded

import "modules/sessions"
import Quickshell
import QtQuick

ShellRoot {
    SessionsModule {}
}
