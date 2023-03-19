import httpx
import os
import asyncio
import aiometer
import tarfile
import shutil

BASE_URL = "https://galaxy.ansible.com/api/v1"
DOWNLOADS_DIR = "downloads"
DATA_DIR = "data"


async def download_tarball(role):
    commit_sha = role['commit']
    owner, repo_name = role['github_user'], role['github_repo']

    if commit_sha is None:
        tarball_url = f"https://codeload.github.com/{owner}/{repo_name}/tar.gz/refs/heads/{role['github_branch']}"
    else:
        tarball_url = f"https://codeload.github.com/{owner}/{repo_name}/tar.gz/{commit_sha}"

    tarball_path = os.path.join(DOWNLOADS_DIR, f"{owner}-{repo_name}-{commit_sha}.tar.gz")

    if os.path.exists(tarball_path):
        print(f"Skipping download for existing file: {tarball_path}")
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(tarball_url, follow_redirects=True, headers={"Authorization": f"Bearer {os.environ.get('GITHUB_API_TOKEN')}"})

    if response.status_code != 200:
        print("Error fetching", response.status_code, tarball_url)
        return

    # Save tarball to a file
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    with open(tarball_path, 'wb') as f:
        f.write(response.content)


async def download_ansible_roles(url):
    roles = []
    while url:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}{url}", headers={'Authorization': f"Bearer {os.environ.get('ANSIBLE_GALAXY_TOKEN')}"})
        if response.status_code != 200:
            print("Error fetching:", url)
            continue

        data = response.json()

        roles.extend(data['results'])

        # Download tarball of source code for the corresponding commit concurrently
        await aiometer.run_on_each(
            download_tarball,
            data['results'],
            max_at_once=5  # Limit concurrent downloads
        )

        # Update the URL for the next request
        url = data['next']

    return roles


def extract_tarball(role):
    owner, repo_name, commit_sha = role['github_user'], role['github_repo'], role['commit']
    tarball_path = os.path.join(DOWNLOADS_DIR, f"{owner}-{repo_name}-{commit_sha}.tar.gz")
    dest_dir = os.path.join(DATA_DIR, owner)

    if not os.path.exists(tarball_path):
        print(f"Skipping extraction for missing file: {tarball_path}")
        return

    with tarfile.open(tarball_path, 'r:gz') as tar:
        # Get the first directory name in the tarball, which should be the repository name
        repo_dir = tar.next().name
        extracted_dir = os.path.join(dest_dir, repo_dir)

        # Remove the extracted directory if it exists
        if os.path.exists(extracted_dir):
            shutil.rmtree(extracted_dir)

        tar.extractall(dest_dir)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    ansible_roles = loop.run_until_complete(download_ansible_roles("/search/roles/?format=json&page_size=1000"))
    print(f"Retrieved {len(ansible_roles)} Ansible roles.")

    for role in ansible_roles:
        commit_sha = role['commit']
        owner, repo_name = role['github_user'], role['github_repo']
        tarball_path = os.path.join(DOWNLOADS_DIR, f"{owner}-{repo_name}-{commit_sha}.tar.gz")
        extract_tarball(role)
