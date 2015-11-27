#! /bin/bash
cd $(git rev-parse --show-toplevel)
compile(){
    echo "Compile .po to .mo"
    django-admin compilemessages
}
collect(){
    echo "Find django translations"
    django-admin makemessages -a --no-wrap --no-obsolete\
        -i node_modules -i bower_components
    echo "Find react translations"
    cd src
    django-admin makemessages -a --no-wrap --no-obsolete\
        -d djangojs -e jsx -e js | sed '/RegExp literal/d'
}

# check if any pofiles have not been compiled
for pofile in `find . -name '*.po'`
do
    mofile=${pofile/%po/mo} # change extention
    [ $mofile -ot $pofile ] && compile && exit # compile and exit if newer
done
collect # run collect if no compilation was needed



