#!/data/data/com.termux/files/usr/bin/bash
# start-audio.sh - start PulseAudio on Termux with speaker + mic modules.
#
# Usage:
#   source start-audio.sh          # start + export PULSE_SERVER into your shell
#   bash start-audio.sh            # start only (export won't reach your shell)
#   bash start-audio.sh --no-mic   # speaker only; releases the mic (see README)
#   bash start-audio.sh --status   # show what is loaded
#   bash start-audio.sh --stop     # kill the daemon
#
# Safe to run many times (idempotent): it only loads what is missing.
#
# NOTE: Termux's portaudio (used by PyAudio) talks to Android OpenSL ES
# directly, NOT through PulseAudio. PulseAudio is for pulse clients
# (paplay, parecord, sox, ffmpeg -f pulse, etc.).

# pactl over the local unix socket (works even before the TCP module exists)
_pa_ctl() { env -u PULSE_SERVER pactl "$@"; }

_pa_main() {
    local mode="start" arg
    for arg in "$@"; do
        case "$arg" in
            --no-mic|--speaker-only) mode="nomic" ;;
            --status) mode="status" ;;
            --stop|--kill) mode="stop" ;;
            -h|--help)
                sed -n '2,16p' "${BASH_SOURCE[0]:-$0}" 2>/dev/null
                return 0 ;;
            *) echo "[!] unknown option: $arg" >&2 ;;
        esac
    done

    if ! command -v pulseaudio >/dev/null 2>&1; then
        echo "[x] pulseaudio not installed. Run: pkg install pulseaudio" >&2
        return 1
    fi

    if [ "$mode" = "stop" ]; then
        pulseaudio --kill >/dev/null 2>&1 && echo "[+] pulseaudio stopped" || echo "[*] pulseaudio was not running"
        return 0
    fi

    # 1) daemon (TCP on localhost so any client can connect via PULSE_SERVER)
    if pulseaudio --check >/dev/null 2>&1; then
        echo "[+] pulseaudio already running"
    else
        echo "[*] starting pulseaudio..."
        if ! pulseaudio --start \
                --load="module-native-protocol-tcp auth-ip-acl=127.0.0.1 auth-anonymous=1" \
                --exit-idle-time=-1 >/dev/null 2>&1; then
            echo "[x] pulseaudio failed to start. Try: pulseaudio -vvv  (to see why)" >&2
            return 1
        fi
        sleep 1
    fi

    export PULSE_SERVER=127.0.0.1

    if ! command -v pactl >/dev/null 2>&1; then
        echo "[!] pactl not found; cannot load extra modules" >&2
        return 0
    fi

    local mods
    mods="$(_pa_ctl list short modules 2>/dev/null)"

    # If daemon was started earlier without the TCP module, add it.
    if ! printf '%s\n' "$mods" | grep -q 'module-native-protocol-tcp'; then
        _pa_ctl load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1 auth-anonymous=1 >/dev/null 2>&1 \
            && echo "[+] loaded module-native-protocol-tcp"
        mods="$(_pa_ctl list short modules 2>/dev/null)"
    fi

    if [ "$mode" = "status" ]; then
        echo "--- modules ---"; printf '%s\n' "$mods" | grep -E 'sles|aaudio|protocol' || true
        echo "--- sinks ---";   _pa_ctl list short sinks 2>/dev/null
        echo "--- sources ---"; _pa_ctl list short sources 2>/dev/null
        return 0
    fi

    # 2) speaker (sink). Termux's default.pa normally loads module-sles-sink.
    if printf '%s\n' "$mods" | grep -qE 'module-(sles|aaudio)-sink'; then
        echo "[+] speaker sink already loaded"
    elif _pa_ctl load-module module-sles-sink >/dev/null 2>&1; then
        echo "[+] loaded module-sles-sink (speaker)"
    elif _pa_ctl load-module module-aaudio-sink >/dev/null 2>&1; then
        echo "[+] loaded module-aaudio-sink (speaker)"
    else
        echo "[!] could not load a speaker sink (sles/aaudio)" >&2
    fi

    # 3) mic (source)
    if [ "$mode" = "nomic" ]; then
        local id
        for id in $(printf '%s\n' "$mods" | awk '/module-(sles|aaudio)-source/ {print $1}'); do
            _pa_ctl unload-module "$id" >/dev/null 2>&1 && echo "[+] unloaded mic module #$id (mic released)"
        done
    elif printf '%s\n' "$mods" | grep -qE 'module-(sles|aaudio)-source'; then
        echo "[+] mic source already loaded"
    elif _pa_ctl load-module module-sles-source >/dev/null 2>&1; then
        echo "[+] loaded module-sles-source (mic)"
    elif _pa_ctl load-module module-aaudio-source >/dev/null 2>&1; then
        echo "[+] loaded module-aaudio-source (mic)"
    else
        echo "[!] mic module failed to load. Usually = no RECORD_AUDIO permission." >&2
        echo "    Fix: install Termux:API app, then run:" >&2
        echo "      termux-microphone-record -d -l 1; sleep 2; termux-microphone-record -q" >&2
        echo "    tap Allow, then run this script again. See README > Troubleshooting." >&2
    fi

    # Make the mic the default source if present
    local src
    src="$(_pa_ctl list short sources 2>/dev/null | awk '$2 !~ /\.monitor$/ {print $2; exit}')"
    if [ -n "$src" ]; then
        _pa_ctl set-default-source "$src" >/dev/null 2>&1 && echo "[+] default source: $src"
    fi

    echo "[+] PULSE_SERVER=$PULSE_SERVER"
    if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then
        echo "    (run 'source start-audio.sh' or 'export PULSE_SERVER=127.0.0.1' to set it in your shell)"
    fi
    return 0
}

_pa_main "$@"
_pa_rc=$?
unset -f _pa_main _pa_ctl
if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then
    exit "$_pa_rc"
else
    unset _pa_rc
    return 0 2>/dev/null || true
fi
