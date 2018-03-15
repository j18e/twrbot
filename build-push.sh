#!/bin/bash -eu

pushd $(dirname $0)

REPO="jamesmacfarlane"
IMAGE="$(basename ${PWD})"
TAG="$1"

docker build -t ${IMAGE}:${TAG} .
docker tag ${IMAGE}:${TAG} ${IMAGE}:latest
docker tag ${IMAGE}:${TAG} ${REPO}/${IMAGE}:${TAG}
docker tag ${IMAGE}:${TAG} ${REPO}/${IMAGE}:latest

docker push ${REPO}/${IMAGE}:${TAG}
docker push ${REPO}/${IMAGE}:latest

git tag "${TAG}"
git push --tags

popd
