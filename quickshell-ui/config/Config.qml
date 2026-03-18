pragma Singleton

import Quickshell

Singleton {
    readonly property SessionsConfig sessions: SessionsConfig {}

    function save(): void {
        // No-op — config persistence deferred to later phase
    }
}
