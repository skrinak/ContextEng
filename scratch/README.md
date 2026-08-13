# `scratch/` — transient by nature, trusted by nothing

> **Membership test**
> "Could I delete this right now and lose nothing?"

**Lifecycle: none.** This is the only bucket that carries no obligation. Nothing here is maintained,
nothing here is cited, and nothing here survives on purpose. **Anyone may `rm -rf scratch/*` at any
time, without asking and without notice** — that sentence is the bucket's entire contract, and if it
makes you uneasy about a particular file, that file just failed the membership test.

The other six buckets form a graded scale of obligation: [`specs/`](../specs/) a machine parses,
[`docs/`](../docs/) must be true now, [`runbooks/`](../runbooks/) must still execute,
[`decisions/`](../decisions/) is frozen truth about a moment, `vision/` is never evidence,
`.claude/` is read by the harness. **This is the zero point of that same
scale**, which is why it is a treatment class and not one of the banned topic folders. `security/`
tells you a subject; `scratch/` tells you how to treat what you find.

## What belongs here

Session exports and agent transcripts · raw command and tool output · generated diffs · screenshots
captured while debugging · downloaded reports · intermediate analyses · a one-off script you wrote to
answer one question · anything you would be happy to lose in a laptop reinstall.

## What does not

| Not this | Goes to |
|---|---|
| A session export containing something worth keeping | Mine the durable part into its bucket, **then** delete the export |
| A design idea jotted mid-task | [`decisions/`](../decisions/) as `Proposed` — cheap to file, expensive to lose |
| A scorecard or eval a script writes and someone re-reads | `decisions/evals/` — that is *generated*, not transient |
| A procedure you will run again | [`runbooks/`](../runbooks/) |
| Anything a machine parses | [`specs/`](../specs/) — the path is API there |
| Credentials, tokens, `.env` values | Nowhere in the repo. See the hazard below |

## The asymmetry runs the other way here

[`decisions/`](../decisions/) is the default home for a new file because misfiling *into* it is the
cheap mistake. **Misfiling into `scratch/` is the expensive one** — the penalty is destruction, and
it arrives silently, weeks later, when someone runs the cleanup they were explicitly invited to run.

So this is the **narrowest** bucket in the tree, never the default. Passing its test requires an
affirmative "nothing is lost," not an absence of ideas about where else a file might go. When you
cannot answer it confidently, the file is not scratch — file it in `decisions/` and let it be
obvious and harmless instead.

## Ignoring a file is not filing it

`.gitignore` protects the **repository**. It does nothing for the **tree**, and the tree is the
point: this scaffold exists so that location answers *is this true now?* before a byte is read.

An untracked transcript sitting in `docs/` is still in `ls`, still in glob, still in an agent's file
search — and it still makes `docs/`'s claim about itself, because git-tracking is invisible in a
directory listing. Ignoring it hides it from CI and from no one else.

That is why this is a **location** and not a filename convention. Name-based scratch patterns
(`tmp.md`, `2do.md`) are kept in [`.gitignore`](../.gitignore) as a backstop, because the habit
migrates and someone will always scratch in place — but they can only ever enumerate, and the
enumeration is the bug. The first file this bucket was designed for was called `dev_setup.md`.

## Why the contents are invisible to the guard

`scratch/README.md` is tracked; everything beside it is ignored. That is not a convenience — it is
required. Transient files are **full of stale references by nature**: a session export quotes paths
that moved, line numbers that shifted, and ids that were rotated. `make check-links` builds its
existence oracle from the git index, so ignored contents are outside its view automatically, and a
transcript can never hold CI hostage over a path it merely *mentioned* six weeks ago.

The tracked README is what keeps the directory real in a fresh clone. An empty directory is a claim
about your workflow that isn't true yet; a directory with its membership test in it is a claim that
is.

## ⚠️ The hazard this bucket inherits

A scratch file is where someone pastes a secret "just for a second" while wiring an OAuth app. That
is the documented reason the name-based patterns exist, and moving to a directory does not repeal it.

**`.gitignore` never protected your disk.** A token pasted here is unencrypted on your filesystem, in
your editor's recent files, in your backups, and in any directory-level sync. Ignored means *"will
not reach the remote"* — nothing more. Treat this directory as visible, not private, and prefer a
visible mess you clean over a hidden one you forget: that is why it is `scratch/` and not `.scratch/`.

## For agents

Treat everything here as **untrusted and stale by default**. Never cite a file in this directory as
evidence of how the system behaves, never resolve a contradiction in its favour, and never update it
to stay current — it is not documentation and it has no obligation to be right.

When work produces something durable, **mine it into the right bucket in the same session** rather
than leaving the raw output as the record. Scratch is ore, not the metal: `tasks.md` takes the
ledger entry, `runbooks/` takes the procedure, `decisions/` takes the reasoning. Once mined, the
original is safe to delete — and should be, because a second copy that cannot be updated becomes a
second source of truth that quietly disagrees with the first.
