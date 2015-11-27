#! /bin/bash
django-admin graph_models -nL en\
    -g cv participants schedule timeclock notes\
    | dot -Tpng > funkytime_models.png
