#!/usr/bin/env bash
#
# Publish one directory to -- or delete one directory from -- the `gh-pages`
# branch, which is what GitHub Pages serves.
#
#   publish-pages.sh publish .        _site   # the production site, at the root
#   publish-pages.sh publish pr-12    _site   # a pull request's preview
#   publish-pages.sh remove  pr-12            # that preview, once the PR closes
#
# One script rather than three inline blocks of git, because all three callers
# have to agree about the parts that are easy to get subtly wrong: what they are
# allowed to delete, that `.nojekyll` has to exist, and that the branch is
# rewritten rather than appended to.
#
# **The branch is a snapshot, not a history.** Every publish force-pushes a
# single orphan commit. The site is ~50 MB of STL/STEP/GLB/PNG and a preview is
# another copy of it, so a branch that accumulated commits would grow by that
# much per push and never give it back -- and nobody has ever wanted to read
# `git log gh-pages`. The cost is that the branch cannot be used to recover an
# older deploy; the source commit it was built from can.
#
# Needs GITHUB_TOKEN, GITHUB_REPOSITORY and GITHUB_SHA from the workflow.
set -euo pipefail

usage() {
    echo "usage: $0 publish <dest> <source-dir> | $0 remove <dest>" >&2
    exit 2
}

[ $# -ge 2 ] || usage
mode=$1
dest=$2

case "$mode" in
publish)
    [ $# -eq 3 ] || usage
    source=$(cd "$3" && pwd)
    ;;
remove)
    [ $# -eq 2 ] || usage
    source=
    ;;
*) usage ;;
esac

# `.` is the site root; anything else is a subdirectory of it. Reject a path
# that could climb out of the checkout, because the next thing this script does
# with it is `rm -rf`.
case "$dest" in
.) ;;
*/* | ..* | /*) echo "refusing dest '$dest': one path segment or '.'" >&2; exit 2 ;;
esac

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required}"
remote="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# One attempt at the whole cycle: clone the branch as it is now, change the one
# directory this call owns, and force-push the result. It is retried from the
# top rather than resumed, because a lost race means the clone is stale and
# everything after it was computed against the wrong tree.
attempt() {
    local site="$work/site"
    rm -rf "$site"

    # --depth 1: the branch is one commit by construction (see above), so there
    # is nothing deeper to fetch. A missing branch is the first-deploy case, not
    # an error.
    if ! git clone --quiet --depth 1 --branch gh-pages "$remote" "$site" 2>/dev/null; then
        echo "gh-pages does not exist yet -- starting an empty site"
        mkdir -p "$site"
        git -C "$site" init --quiet
        git -C "$site" remote add origin "$remote"
    fi

    if [ "$dest" = "." ]; then
        # Production replaces the root *except* for the previews: a deploy of
        # `main` must not take every open PR's preview down with it.
        find "$site" -mindepth 1 -maxdepth 1 \
            ! -name .git ! -name 'pr-*' -exec rm -rf {} +
    else
        rm -rf "${site:?}/$dest"
    fi

    if [ -n "$source" ]; then
        mkdir -p "$site/$dest"
        cp -R "$source"/. "$site/$dest"/
    fi

    # Pages runs Jekyll on a branch source unless this file exists, and Jekyll
    # drops every path starting with `_` or `.` on its way out.
    touch "$site/.nojekyll"

    git -C "$site" config user.name "github-actions[bot]"
    git -C "$site" config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git -C "$site" checkout --quiet --orphan snapshot
    git -C "$site" add -A

    # Nothing to say: the tree we would push is byte-for-byte what is already
    # served. Pushing anyway would spend a Pages rebuild to publish no change.
    local old new
    old=$(git -C "$site" rev-parse 'origin/gh-pages^{tree}' 2>/dev/null || echo none)
    git -C "$site" commit --quiet --allow-empty \
        -m "$mode $dest from ${GITHUB_SHA:-unknown}"
    new=$(git -C "$site" rev-parse 'HEAD^{tree}')
    if [ "$old" = "$new" ]; then
        echo "gh-pages already matches this tree -- nothing to push"
        return 0
    fi

    git -C "$site" push --quiet --force origin snapshot:gh-pages
    echo "pushed $mode of '$dest' to gh-pages"
}

# The three callers serialise on one Actions concurrency group, so a race needs
# two workflows the group did not cover -- a manual push to gh-pages, say. Cheap
# insurance either way, since losing the race costs a rebuilt site.
for try in 1 2 3; do
    if attempt; then
        exit 0
    fi
    echo "attempt $try failed; retrying" >&2
    sleep $((try * 5))
done
echo "could not publish to gh-pages after 3 attempts" >&2
exit 1
