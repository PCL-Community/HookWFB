const express = require('express');
const bodyParser = require('body-parser');
const { Octokit } = require('@octokit/rest');

const app = express();
const port = process.env.PORT || 3000;

// GitHub token and repository details
//here you can use your token 
const GITHUB_TOKEN = 'your_github_token';
const octokit = new Octokit({ auth: GITHUB_TOKEN });

app.use(bodyParser.json());

app.post('/webhook', async (req, res) => {
  const event = req.headers['x-github-event'];
  const payload = req.body;

  try {
    if (event === 'pull_request') {
      const action = payload.action;
      const prNumber = payload.pull_request.number;
      const repoOwner = payload.repository.owner.login;
      const repoName = payload.repository.name;

      if (action === 'closed' && payload.pull_request.merged) {
        // PR merged
        await octokit.issues.addLabels({
          owner: repoOwner,
          repo: repoName,
          issue_number: prNumber,
          labels: ['√ 完成']
        });
      } else if (action === 'closed' && !payload.pull_request.merged) {
        // PR closed without merging
        await octokit.issues.addLabels({
          owner: repoOwner,
          repo: repoName,
          issue_number: prNumber,
          labels: ['× 拒绝']
        });
      } else if (action === 'created') {
        // PR created
        await octokit.pulls.requestReviewers({
          owner: repoOwner,
          repo: repoName,
          pull_number: prNumber,
          reviewers: ['WForst-Breeze']
        });
      }
    } else if (event === 'pull_request_review') {
      const review = payload.review;
      const prNumber = payload.pull_request.number;
      const repoOwner = payload.repository.owner.login;
      const repoName = payload.repository.name;

      if (review.state === 'approved' && review.user.login === 'WForst-Breeze') {
        await octokit.issues.addLabels({
          owner: repoOwner,
          repo: repoName,
          issue_number: prNumber,
          labels: ['⇵ 通过']
        });
      }
    }

    res.status(200).send('Webhook processed');
  } catch (error) {
    console.error('Error processing webhook:', error);
    res.status(500).send('Internal Server Error');
  }
});

app.listen(port, () => {
  console.log(`Webhook server is listening on port ${port}`);
});

