# Anonymous-release checklist

Before transferring this repository to an anonymous hosting service:

- [ ] `scripts/audit_release.py` reports zero content violations.
- [ ] If repository history will be exposed, `scripts/audit_release.py --include-git` also reports zero violations. Otherwise, export a working-tree archive that excludes `.git` and verify the archive contents before upload.
- [ ] Git author and committer identities are `Anonymous Authors` with the neutral invalid-domain address.
- [ ] README and package metadata contain no author, affiliation, acknowledgment, personal URL, or citation entry.
- [ ] Files contain no local home-directory path, private network address, internal hostname, credential, or repository-owner handle.
- [ ] Document and archive metadata contain no local account name.
- [ ] The anonymous host does not expose the source repository URL, owner, fork relation, or transfer history.
- [ ] Issue trackers, Actions logs, release assets, and branch names are checked separately before being made visible.
- [ ] Citation metadata and acknowledgments are added only after the double-blind period ends.

The legacy dataset-construction date stored in benchmark source context is not an author identifier and should remain intact.
