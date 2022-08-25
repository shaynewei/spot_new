#!/bin/bash

FUNC=spot_advisor
FOLDER=$(cd `dirname $0`; pwd)


if [ "$1" != "rebuild"  ]; then
    zip -r9 -g $FUNC.zip $FUNC.py
    aws lambda update-function-code \
        --function-name	$FUNC \
        --zip-file fileb://$FUNC.zip
    exit 0
fi

if [ -e "$FOLDER/$FUNC.zip" ]; then
    rm $FOLDER/$FUNC.zip
fi

. $FOLDER/venv/bin/activate

cd $VIRTUAL_ENV/lib/python3.7/site-packages/
zip -r9 $FOLDER/$FUNC.zip .

deactivate
cd $FOLDER
zip -r9 -g $FUNC.zip $FUNC.py

aws lambda update-function-code \
    --function-name $FUNC \
    --zip-file fileb://$FUNC.zip

