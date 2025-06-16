#!/bin/bash

# Script to manually create a release from existing tag
# Usage: ./create_release.sh v1.0.0

TAG=$1

if [ -z "$TAG" ]; then
    echo "Usage: $0 <tag_name>"
    echo "Example: $0 v1.0.0"
    exit 1
fi

echo "Creating release for tag: $TAG"

# Re-push the tag to trigger the workflow
git push origin $TAG --force

echo "Tag pushed. Check GitHub Actions to see if the workflow runs."
echo "If it doesn't work, you can create the release manually at:"
echo "https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^./]*\).*/\1\/\2/')/releases/new?tag=$TAG"
