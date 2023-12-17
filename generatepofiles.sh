#!/bin/bash
mkdir -p locale/
LANGUAGES_LIST=(es)
for lang in "${LANGUAGES_LIST[@]}"
do
  echo "${lang}"
  mkdir -p locale/"${lang}"/LC_MESSAGES/
  LANG_PO="locale/"${lang}"/LC_MESSAGES/extremecooling4linux.po"
  LANG_MO="locale/"${lang}"/LC_MESSAGES/extremecooling4linux.mo"
  TEMPLATE_POT="locale/extremecooling4linux.pot"
  xgettext --from-code=UTF-8 ec4Linux.py data/glade_files/mainui.glade --sort-output -o $TEMPLATE_POT
  if [ -f "$LANG_PO" ]; then
    echo "update $LANG_PO file"
    msgmerge --update $LANG_PO $TEMPLATE_POT
  else
    echo "create $LANG_PO file"
    msginit --input=$TEMPLATE_POT --locale="${lang}" --output=$LANG_PO
  fi
  msgfmt --output-file=$LANG_MO $LANG_PO
done

