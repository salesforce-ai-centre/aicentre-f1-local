# GitHub Repository Setup Instructions

Follow these steps to create a new GitHub repository and push this code to it:

## Creating the GitHub Repository

1. Go to [GitHub](https://github.com/) and sign in to your account
2. Click on the "+" icon in the top-right corner and select "New repository"
3. In the "Owner" dropdown, select the "Salesforce AI Centre" organization
4. Enter "aicentre-f1-local" as the Repository name
5. Add a description: "F1 Telemetry Dashboard with AI Race Engineer - Local Version for F1 24 Game"
6. Choose "Private" for the repository visibility
7. Do not initialize the repository with any files (no README, .gitignore, or license)
8. Click "Create repository"

## Pushing Your Local Code to GitHub

After creating the repository, you'll see instructions for pushing an existing repository. Follow these steps:

```bash
# Go to your local project directory
cd /Users/jacob.berry/aicentre-f1

# Set the remote URL (replace with the actual URL from GitHub)
git remote add origin https://github.com/Salesforce-AI-Centre/aicentre-f1-local.git

# Push your code to GitHub
git push -u origin master
```

You may need to authenticate with GitHub during this process.

## Verifying the Repository

After pushing, visit the repository URL to verify that all files have been uploaded correctly:
https://github.com/Salesforce-AI-Centre/aicentre-f1-local

## Adding Team Members

1. Go to the repository on GitHub
2. Click on "Settings" > "Collaborators and teams"
3. Click "Add teams" or "Add people" to add team members
4. Grant appropriate permissions (Read, Triage, Write, Maintain, or Admin)

## Repository Protection (Optional)

For additional security:

1. Go to "Settings" > "Branches"
2. Add a branch protection rule for the master branch
3. Enable options like "Require pull request reviews before merging" and "Require status checks to pass before merging"