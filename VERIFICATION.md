# Verification

Run the automated checks documented in [INSTALL.md](INSTALL.md). CI validates
the repository's unit, CLI, and documentation checks for each source revision.
Docker-dependent tests are reported separately when the required runtime is
unavailable.

Automated checks cover the local laboratory workflow and synthetic cases. They
do not establish production deployment security, tenant isolation on an
external host, identity-provider integration, or operational recovery. Validate
those properties on a separate controlled system before deployment.
