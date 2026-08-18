# Publishing Browser GIFs

Remote publication changes repository or pull-request state. Perform it only when explicitly requested.

## Choose the Repository's Mechanism

Read contribution and asset rules first. Prefer an established documentation asset directory, release asset workflow, issue attachment mechanism, object store, or dedicated media branch already used by the project.

If the repository has no policy, ask before creating a branch or uploading to an external service. Never upload private screenshots to an unrelated third-party host without permission.

## Dedicated Media Branch

When the repository explicitly uses a non-merging media branch:

- work in a separate scratch checkout;
- verify the branch contains only intended media;
- compare the staged file checksum with the locally verified GIF;
- append commits rather than rewriting published history;
- do not commit binary media to the feature branch unless repository policy requires it.

## Pull-Request Attachment

Immediately before editing the pull request, re-read its live head and compare it with the commit demonstrated by the GIF. Re-record when the head moved in a way that changes the demonstrated behavior.

After publication, verify the authenticated asset response, content type, byte size, and rendered pull-request body. Record the demonstrated commit, tree or origin, mode flags, backend or fixture status, and any browser-state exceptions next to the embed.

Do not claim public availability when verification used repository-member authentication.
