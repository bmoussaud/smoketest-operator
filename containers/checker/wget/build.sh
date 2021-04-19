#!/usr/bin/env bash

# If we're building a tag, map it to the upstream tags. Otherwise use develop.
if grep '^v[0-9.]\+$' <<< "${SOURCE_BRANCH}" &>/dev/null; then
    VERSION="${SOURCE_BRANCH}"
else
    VERSION="develop"
fi

echo "${VERSION}"
docker build \
    --label org.label-schema.build-date=`date -u +"%Y-%m-%dT%H:%M:%SZ"` \
    --label org.label-schema.vcs-ref=`git rev-parse --short HEAD` \
    --label org.label-schema.vcs-url="https://github.com/bmoussaud/katapul/smoke" \
    --label org.label-schema.version="${SOURCE_BRANCH}" \
    --label org.label-schema.schema-version="1.0" \
    --build-arg VERSION="${VERSION}" \
    -f "${DOCKERFILE_PATH}" \
    -t "${IMAGE_NAME}" \
    .