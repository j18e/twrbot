#!/bin/bash -eu

pushd $(dirname $0)

IMAGE="jamesmacfarlane/$(basename ${PWD})"
TAG="$1"

docker build -t ${IMAGE}:${TAG} \
    -t ${IMAGE}:latest .
docker push ${IMAGE}

popd
