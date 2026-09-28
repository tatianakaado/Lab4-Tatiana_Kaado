# Finish GitHub setup and Lab 4 submission

The application and README are prepared locally. GitHub publishing requires
your own account. No GitHub repository, push, release, invitation, or Moodle
submission is implied by this guide.

## Solo workflow

Open this project folder in VS Code, then open its integrated terminal.

1. The local repository is initialized on `main`, with the integration
   committed and tagged `v1.0`. The repository-specific identity is
   `Tatiana Kaado <tgk12@mail.aub.edu>`, as supplied by the student. Review it:

   ```bash
   git status
   git log --oneline --decorate
   git remote -v
   ```

2. The prepared commit contains the combined application, tests, and README.
   If you make further changes, stage and commit those changes before pushing.

3. Create an empty repository named `Lab4-Tatiana_Kaado` on GitHub. Choose
   private visibility if required by your course. Leave GitHub's README,
   .gitignore, and license initialization options unchecked because this
   local project already contains its files.

4. The remote is already configured for `tatianakaado`; push the local commit:

   ```bash
   git push -u origin main
   ```

   Complete GitHub authentication locally when prompted. A GitHub account
   password is not used as a Git HTTPS password. VS Code also provides
   **Publish to GitHub** from Source Control after you sign in.

5. Open the repository on GitHub and verify both GUI files, `school_mgmt/`,
   tests, README, and the commit are visible.

6. The optional local `v1.0` tag has already been created. Publish it with:

   ```bash
   git push origin v1.0
   ```

   A GitHub Release is optional for solo students; create it from this tag
   if desired.

7. For a private repository, add the instructor/TAs using the accounts they
   provide. Submit your repository link and README on Moodle as requested by
   the handout. The solo workflow does not require a “who pushed what” file.

For later changes, review `git diff`, stage the relevant files, commit with a
message describing the change, and run `git push`. `git log --oneline` shows
recorded versions; `git status` shows staged and unstaged changes.

## If working with a partner

Use the team workflow in the handout before the first upload: agree on roles,
create a shared repository, invite your partner, and develop on
`feature-tkinter` and `feature-pyqt`. Each student commits and pushes their own
work, opens a pull request, reviews the other part, and merges it into `main`.
Test the integration, tag `v1.0`, create a GitHub Release, and document actual
contributions. Do not claim collaborative history for files prepared locally
by one person.

## References

- Course requirements: the supplied `Lab 4-Git.docx`.
- [GitHub: adding locally hosted code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
- [VS Code source control](https://code.visualstudio.com/docs/sourcecontrol/overview)
- Assigned tutorial: https://www.w3schools.com/git/
