#!/usr/bin/env python3
"""
Advanced GitHub README Updater using GraphQL API
Provides more detailed information and better performance
"""

import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, Any
import urllib.parse

class AdvancedGitHubUpdater:
    def __init__(self, token: str, username: str):
        self.token = token
        self.username = username
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.graphql_url = 'https://api.github.com/graphql'
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        response = requests.post(
            self.graphql_url,
            headers=self.headers,
            json={'query': query}
        )
        response.raise_for_status()
        return response.json()
    
    def get_user_activity(self) -> Dict[str, Any]:
        """Get comprehensive user activity using GraphQL"""
        query = f"""
        {{
          user(login: "{self.username}") {{
            # Recent starred repositories
            starredRepositories(first: 5, orderBy: {{field: STARRED_AT, direction: DESC}}) {{
              edges {{
                starredAt
                node {{
                  name
                  owner {{
                    login
                  }}
                  description
                  url
                  stargazerCount
                  primaryLanguage {{
                    name
                    color
                  }}
                  forkCount
                  issues {{
                    totalCount
                  }}
                }}
              }}
            }}
            
            # Recent pull requests
            pullRequests(first: 5, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
              nodes {{
                title
                url
                state
                createdAt
                merged
                repository {{
                  name
                  owner {{
                    login
                  }}
                }}
                additions
                deletions
                changedFiles
              }}
            }}
            
            # Recent repositories with commits
            repositories(first: 10, orderBy: {{field: PUSHED_AT, direction: DESC}}, privacy: PUBLIC) {{
              nodes {{
                name
                url
                pushedAt
                defaultBranchRef {{
                  target {{
                    ... on Commit {{
                      history(first: 1, author: {{emails: ["{self.username}@users.noreply.github.com"]}}) {{
                        nodes {{
                          message
                          committedDate
                          url
                          abbreviatedOid
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            
            # Contribution statistics
            contributionsCollection {{
              totalCommitContributions
              totalPullRequestContributions
              totalIssueContributions
              totalPullRequestReviewContributions
              contributionCalendar {{
                totalContributions
                weeks {{
                  contributionDays {{
                    contributionCount
                    date
                  }}
                }}
              }}
            }}
          }}
        }}
        """
        
        return self.execute_query(query)
    
    def format_starred_with_details(self, data: Dict) -> str:
        """Format starred repositories with rich details"""
        starred = data['data']['user']['starredRepositories']['edges']
        
        if not starred:
            return "No recent starred repositories"
        
        lines = []
        for edge in starred:
            repo = edge['node']
            lang = repo['primaryLanguage']
            # lang_badge = f"![{lang['name']}](https://img.shields.io/badge/-{lang['name']}-{lang['color']}?style=flat-square)" if lang else ""
            lang_badge = f"![{urllib.parse.quote(lang['name'])}](https://img.shields.io/badge/{urllib.parse.quote(lang['name'])}-{lang['color']}?style=for-the-badge)" if lang else ""
            
            lines.append(f"- ⭐ [{repo['owner']['login']}/{repo['name']}]({repo['url']}) {lang_badge}")
            if repo['description']:
                lines.append(f"  - 📝 {repo['description'][:100]}...")
            lines.append(f"  - 📊 Stars: {repo['stargazerCount']:,} | Forks: {repo['forkCount']:,} | Issues: {repo['issues']['totalCount']}")
            lines.append(f"  - ⏰ Starred: {edge['starredAt'][:10]}")
            lines.append("")
        
        return '\n'.join(lines[:-1])  # Remove last empty line
    
    def format_prs_with_stats(self, data: Dict) -> str:
        """Format pull requests with statistics"""
        prs = data['data']['user']['pullRequests']['nodes']
        
        if not prs:
            return "No recent pull requests"
        
        lines = []
        for pr in prs:
            state_emoji = "🟢" if pr['state'] == 'OPEN' else ("🟣" if pr['merged'] else "🔴")
            
            lines.append(f"- {state_emoji} [{pr['title']}]({pr['url']})")
            lines.append(f"  - 📁 Repository: {pr['repository']['owner']['login']}/{pr['repository']['name']}")
            lines.append(f"  - 📈 Changes: +{pr['additions']} -{ pr['deletions']} in {pr['changedFiles']} files")
            lines.append(f"  - 📅 Created: {pr['createdAt'][:10]}")
            lines.append("")
        
        return '\n'.join(lines[:-1])
    
    def format_recent_commits_from_repos(self, data: Dict) -> str:
        """Format recent commits from user's repositories"""
        repos = data['data']['user']['repositories']['nodes']
        
        commits = []
        for repo in repos:
            if repo['defaultBranchRef'] and repo['defaultBranchRef']['target']['history']['nodes']:
                commit = repo['defaultBranchRef']['target']['history']['nodes'][0]
                commits.append({
                    'repo_name': repo['name'],
                    'repo_url': repo['url'],
                    'message': commit['message'].split('\n')[0][:80],
                    'sha': commit['abbreviatedOid'],
                    'url': commit['url'],
                    'date': commit['committedDate'][:10]
                })
        
        if not commits:
            return "No recent commits found"
        
        # Sort by date and take top 5
        commits.sort(key=lambda x: x['date'], reverse=True)
        commits = commits[:5]
        
        lines = []
        for commit in commits:
            lines.append(f"- 💾 [`{commit['sha']}`]({commit['url']}) - {commit['message']}")
            lines.append(f"  - 📦 Repo: [{commit['repo_name']}]({commit['repo_url']}) | 📅 Date: {commit['date']}")
            lines.append("")
        
        return '\n'.join(lines[:-1])
    
    def format_contribution_stats(self, data: Dict) -> str:
        """Format contribution statistics"""
        stats = data['data']['user']['contributionsCollection']
        calendar = stats['contributionCalendar']
        
        # Calculate streak
        streak = 0
        current_streak = 0
        for week in reversed(calendar['weeks']):
            for day in reversed(week['contributionDays']):
                if day['contributionCount'] > 0:
                    current_streak += 1
                    streak = max(streak, current_streak)
                else:
                    if current_streak > 0:
                        break
                    current_streak = 0
        
        lines = [
            f"- 📊 **Total Contributions:** {calendar['totalContributions']:,}",
            f"- 💻 **Commits:** {stats['totalCommitContributions']:,}",
            f"- 🔀 **Pull Requests:** {stats['totalPullRequestContributions']:,}",
            f"- 🐛 **Issues:** {stats['totalIssueContributions']:,}",
            f"- 👀 **Code Reviews:** {stats['totalPullRequestReviewContributions']:,}",
            f"- 🔥 **Current Streak:** {current_streak} days"
        ]
        
        return '\n'.join(lines)
    
    def update_readme_advanced(self, readme_path: str = 'README.md'):
        """Update README with advanced GraphQL data"""
        print("Fetching comprehensive GitHub data via GraphQL...")
        
        try:
            data = self.get_user_activity()
            
            # Check for errors
            if 'errors' in data:
                print(f"GraphQL errors: {data['errors']}")
                return False
            
            # Format all sections
            sections = {
                'stars': self.format_starred_with_details(data),
                'prs': self.format_prs_with_stats(data),
                'commits': self.format_recent_commits_from_repos(data),
                'stats': self.format_contribution_stats(data)
            }
            
            # Read current README
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
            except FileNotFoundError:
                readme_content = ""
            
            # Define markers
            markers = {
                'stars': ('<!-- STARS:START -->', '<!-- STARS:END -->'),
                'prs': ('<!-- PRS:START -->', '<!-- PRS:END -->'),
                'commits': ('<!-- COMMITS:START -->', '<!-- COMMITS:END -->'),
                'stats': ('<!-- STATS:START -->', '<!-- STATS:END -->')
            }
            
            # Update each section
            for section, content in sections.items():
                start_marker, end_marker = markers[section]
                pattern = f'{re.escape(start_marker)}.*?{re.escape(end_marker)}'
                replacement = f'{start_marker}\n{content}\n{end_marker}'
                
                if start_marker in readme_content:
                    readme_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
                else:
                    # Add section with appropriate header
                    headers = {
                        'stars': '## 🌟 Latest Starred Repositories',
                        'prs': '## 🔀 Recent Pull Requests',
                        'commits': '## 📝 Recent Commits',
                        'stats': '## 📊 Contribution Statistics'
                    }
                    readme_content += f'\n\n{headers.get(section, "## " + section.title())}\n\n{start_marker}\n{content}\n{end_marker}'
            
            # Update timestamp
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            timestamp_marker_start = '<!-- UPDATED:START -->'
            timestamp_marker_end = '<!-- UPDATED:END -->'
            timestamp_pattern = f'{re.escape(timestamp_marker_start)}.*?{re.escape(timestamp_marker_end)}'
            timestamp_replacement = f'{timestamp_marker_start}\n🔄 Last updated: {timestamp}\n{timestamp_marker_end}'
            
            if timestamp_marker_start in readme_content:
                readme_content = re.sub(timestamp_pattern, timestamp_replacement, readme_content, flags=re.DOTALL)
            else:
                readme_content += f'\n\n---\n\n{timestamp_marker_start}\n🔄 Last updated: {timestamp}\n{timestamp_marker_end}'
            
            # Write updated README
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"✅ README updated successfully with advanced data at {timestamp}")
            return True
            
        except Exception as e:
            print(f"Error updating README: {e}")
            return False

def main():
    token = os.environ.get('GH_TOKEN')
    username = os.environ.get('GITHUB_USERNAME')
    
    if not token or not username:
        print("Error: Required environment variables not set")
        return 1
    
    updater = AdvancedGitHubUpdater(token, username)
    
    if updater.update_readme_advanced():
        return 0
    return 1

if __name__ == '__main__':
    exit(main())
