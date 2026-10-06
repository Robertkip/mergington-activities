# GitHub setup

Some of this repository's protections live in GitHub settings, not in files. This page covers those settings, the stand-in values to replace before you push, and how personal and organization repositories differ.

## Values to replace before pushing

The files use stand-in values so they work as examples. Replace each one with the real value.

| Stand-in | Appears in | Replace with |
|---|---|---|
| `mergington-high-school` | .github/CODEOWNERS | The name of your GitHub organization |
| `maintainers`, `backend`, `frontend` | .github/CODEOWNERS | The slugs of your three teams |
| `conduct@mergington-high-school.example` | CODE_OF_CONDUCT.md | The address that receives conduct reports |
| `security@mergington-high-school.example` | SECURITY.md | The address that receives security reports |
| 3 business days | SECURITY.md | How quickly you can acknowledge a report |
| 5 business days | SECURITY.md | How quickly you can review a security update |

Do this before you push. GitHub skips a code owner that does not exist or lacks access, so with the stand-in names nobody is assigned and Code Owner review protects nothing. The `.example` addresses can never receive mail, so a report sent to one is lost.

## One-time setup

Do these steps in order. Creating teams needs an organization owner. The rest needs admin access to the repository.

1. **Create the repository** in your organization on GitHub and push `main` to it.
2. **Create three teams** named `maintainers`, `backend` and `frontend`. Click your profile picture, then **Organizations**, choose your organization, click **Teams**, then **New team**. Under **Team visibility**, choose the visible option, because a team can only be a code owner if it is visible. Put at least two people in each team: authors cannot approve their own pull requests, so a team of one cannot get its own changes merged.
3. **Give each team Write access.** In the repository, open **Settings**, click **Collaborators & teams** in the Access section of the sidebar, click **Add teams**, pick the team, choose the **Write** role under "Choose a role" and add it. GitHub requires the team itself to have write permission, even if its members already have it.
4. **Import the ruleset.** In the repository, open **Settings**, then **Rules** and **Rulesets** in the sidebar (GitHub's documentation has used both "Rules" and "Rulesets" for the top-level menu). Click **New ruleset**, then **Import a ruleset**, choose `.github/rulesets/protect-main.json`, review it and click **Create**. Confirm it is listed as active. Rulesets are available in public repositories on every plan, and in private repositories on GitHub Pro, GitHub Team and GitHub Enterprise Cloud. A private repository on the Free plan cannot use them.
5. **Turn on Dependabot.** In **Settings**, open **Advanced Security** (under "Security and quality" in the sidebar). Click **Enable** next to **Dependabot alerts**, then next to **Dependabot security updates**. Security updates need alerts to be on first. Weekly version updates need no setting: they start once `.github/dependabot.yml` is on the default branch.
6. **Turn on private vulnerability reporting.** On the same page, click **Enable** next to **Private vulnerability reporting**. GitHub documents this feature for public repositories. If your repository is private, skip this step: reporters use the email address in SECURITY.md instead. Once it is on, reporters see a **Report a vulnerability** button on the repository's **Advisories** page.
7. **Check CODEOWNERS.** Open `.github/CODEOWNERS` on GitHub. Any invalid line is highlighted as an error. There should be none.

## Check that it works

Once the ruleset is active, confirm each protection with a throwaway branch:

- A direct push to `main` is rejected.
- A force push to `main` is rejected.
- A pull request that changes only a file in `src/static/` asks the frontend team for review and cannot be merged until a frontend owner approves.
- A pull request with an unresolved review conversation cannot be merged.
- Anyone with read access can see the active rules by adding `/rules` to the repository URL, for example `https://github.com/<organization>/<repository>/rules`.

The ruleset has no bypass list, so these rules apply to organization owners and administrators too, and nobody can rename or delete `main` while the ruleset is active. If you ever need to, set the ruleset to disabled in its settings first and turn it back on afterwards.

## Personal vs organization repositories

This repository is set up for an organization. If it stayed in a personal account, these things would be different:

| | Personal account | Organization |
|---|---|---|
| Access levels | Two: the owner and collaborators. Collaborators cannot have read-only access to a private repository. | Five roles, from least to most access: Read, Triage, Write, Maintain and Admin. |
| Adding people | Invite each person as an individual collaborator. | Add people to teams and give each team a role on the repository. |
| CODEOWNERS | Can name individual users and email addresses. | Can also name teams, such as `@mergington-high-school/backend`. |
| Rulesets | Per repository. | Per repository, plus organization-level rulesets that cover several repositories at once (on plans that include them). |
| When someone leaves | The repository belongs to one person. | Organization owners have admin access to every repository, so nothing depends on one person. |

GitHub also limits how many people can be invited to a repository within 24 hours, and suggests creating an organization to collaborate with more people.

## Sources

Checked against GitHub's documentation on 2026-10-06:

- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Managing rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository)
- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [REST API: rules](https://docs.github.com/en/rest/repos/rules) (the ruleset JSON fields)
- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews)
- [Creating an organization team](https://docs.github.com/en/organizations/organizing-members-into-teams/creating-a-team)
- [Managing teams and people with access to your repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-teams-and-people-with-access-to-your-repository)
- [Repository roles for an organization](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization)
- [Permission levels for a personal account repository](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-user-account-settings/permission-levels-for-a-personal-account-repository)
- [Configuring Dependabot alerts](https://docs.github.com/en/code-security/dependabot/dependabot-alerts/configuring-dependabot-alerts)
- [Configuring Dependabot security updates](https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/configuring-dependabot-security-updates)
- [Dependabot options reference](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)
- [Configuring private vulnerability reporting for a repository](https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository)
