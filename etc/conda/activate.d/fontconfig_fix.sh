# Fix fontconfig cache issue by using a local / temp one

FONTCONFIG_LOCAL=${CONDA_PREFIX}/var/cache/fontconfig

if [ ! -d "$FONTCONFIG_LOCAL" -a -w "$CONDA_PREFIX" ]; then
    mkdir -p "$FONTCONFIG_LOCAL"
fi
if [ ! -d "$FONTCONFIG_LOCAL" ]; then
    FONTCONFIG_LOCAL="${XDG_CACHE_HOME:-$HOME/.cache}/fontconfig$(echo $CONDA_PREFIX | sed 's|/|-|g')"
    mkdir -p "$FONTCONFIG_LOCAL"
    chmod a+rwx "$FONTCONFIG_LOCAL"
fi
export FONTCONFIG_LOCAL

if [ ! -e "$FONTCONFIG_LOCAL/conf/fontconfig" ]; then
    mkdir -p "$FONTCONFIG_LOCAL/conf/fontconfig"
    mkdir -p "$FONTCONFIG_LOCAL/fontconfig_cache"
    if [ -f /etc/fonts/fonts.conf ]; then
        sed "s/^.*<cachedir.*$//" /etc/fonts/fonts.conf > "$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
        sed -i "/^.*<\!-- Font cache directory list.*$/a\\\t<cachedir>$FONTCONFIG_LOCAL\/fontconfig_cache<\/cachedir>" "$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
    else
        # this does not work actually if /etc/fonts/fonts.conf exists
        cat << EOF > "$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
    <cachedir>$FONTCONFIG_LOCAL/fontconfig_cache</cachedir>
    <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
</fontconfig>
EOF
    fi
fi
export FONTCONFIG_FILE="$FONTCONFIG_LOCAL/conf/fontconfig/fonts.conf"
