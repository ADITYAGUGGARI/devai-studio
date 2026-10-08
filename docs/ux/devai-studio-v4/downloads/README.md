# Restore the original downloadable package

Every byte of the original revision 4 ZIP and self-contained HTML gallery is retained in these numbered parts. The connected GitHub upload route timed out on the large archive. Individual design sources and a lightweight gallery are also available directly in the parent directory.

After cloning the repository, run from its root:

```bash
python3 docs/ux/devai-studio-v4/restore-downloads.py
```

This creates `downloads/restored/DevAI-Studio-UX-Handoff.zip` and `downloads/restored/DevAI-Studio-UX-Gallery.html`. Each part and final file must match the SHA-256 checksum and byte size in manifest.json. The files are byte-for-byte identical to the delivered revision 4 downloads. Open the restored HTML locally, or extract the ZIP for the engineering handoff and all individual sources.

To choose an output folder:

```bash
python3 docs/ux/devai-studio-v4/restore-downloads.py --output-dir /tmp/devai-ux-downloads
```

The restore utility uses only Python's standard library. It makes no network requests and does not modify the application.
