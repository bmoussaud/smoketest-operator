#!/bin/sh
PREFIX="### CHECKER WGET"
echo "${PREFIX} go"

if [ $START_DELAY_SECS -ne 0 ]; then
echo Waiting $START_DELAY_SECS seconds
sleep $START_DELAY_SECS
fi

for i in `seq 1 $MAX_RETRIES`
do
RESPONSE_FILE=/tmp/http-response.$$
rm -f $RESPONSE_FILE

wgetCmdLine="wget --timeout=${TIMEOUT} -O $RESPONSE_FILE ${URL}"

echo "Executing ${wgetCmdLine}"
${wgetCmdLine}

WGET_EXIT_CODE=$?
if [ $WGET_EXIT_CODE -eq 0 ]; then
break
fi
sleep $RETRY_INTERVAL_SECS
done

if [ $WGET_EXIT_CODE -ne 0 ]; then
echo "ERROR: ${URL} returned non-200 response code (${WGET_EXIT_CODE})"
exit $WGET_EXIT_CODE
fi

if [ $SHOW_PAGE_CONTENT -ne 0 ]; then
echo "--------------------------------------"
cat $RESPONSE_FILE
echo "--------------------------------------"
fi

if [ ${#EXPECTED_RESPONSE_TEXT} -ne 0 ]; then
echo Making sure response contains: "${EXPECTED_RESPONSE_TEXT}"
grep "${EXPECTED_RESPONSE_TEXT}" $RESPONSE_FILE

SEARCH_EXIT_CODE=$?

    if [ $SEARCH_EXIT_CODE -ne 0 ]; then
    echo ERROR: Response body did not contain: "${EXPECTED_RESPONSE_TEXT}"
    exit $SEARCH_EXIT_CODE
    else
    echo "FOUND"
    fi
fi

