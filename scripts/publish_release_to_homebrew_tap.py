import argparse
import hashlib
import os
import subprocess

HOMEBREW_TAP_PATH = './homebrew-tap'


def clone_homebrew_tap_repo():
    subprocess.run(['git', 'clone', 'https://github.com/QtonSolutions/homebrew-tap.git'])


def generate_sha256_digest(archive_path):
    sha256 = hashlib.sha256()

    with open(archive_path, 'rb') as archive_path:
        file_buffer_size = 64 * 1024
        while True:
            data = archive_path.read(file_buffer_size)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()


def write_updated_brew_formula(version, sha256_digest):
    with open('homebrew-tap/Formula/sessh.rb', 'w') as formula_file:
        formula = f'''class Sessh < Formula
    homepage "https://github.com/QtonSolutions/sessh"
    url "https://github.com/QtonSolutions/sessh/releases/download/{version}/sessh-{version}-osx.gz"
    sha256 "{sha256_digest}"

    bottle :unneeded

    def install
        bin.install "sessh"
    end

    test do
        assert_match version.to_s, shell_output("#{bin}/sessh --version")
    end
end'''
        formula_file.write(formula)


def commit_and_push(version):
    subprocess.run(['git', 'add', 'Formula/sessh.rb'], cwd=HOMEBREW_TAP_PATH)
    subprocess.run(['git', 'commit', '-m', f'Publish {version}'], cwd=HOMEBREW_TAP_PATH)
    subprocess.run(['git', 'push'], cwd=HOMEBREW_TAP_PATH)


def set_up_github_credentials():
    github_auth_token = os.environ["GH_TOKEN"]
    subprocess.run(['git', 'config', 'credential.helper', 'store --file=.git/credentials'], cwd=HOMEBREW_TAP_PATH)
    with open(os.path.join(HOMEBREW_TAP_PATH, '.git/credentials'), 'w') as credentials_file:
        credentials_file.write(f'https://{github_auth_token}:@github.com')
    subprocess.run(['git', 'config', '--local', 'user.name', 'Travis CI'], cwd=HOMEBREW_TAP_PATH)
    subprocess.run(['git', 'config', '--local', 'user.email', 'travis@travis-ci.org'], cwd=HOMEBREW_TAP_PATH)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Publish new release to QtonSolutions Homebrew tap")
    parser.add_argument('version', help="version tag")
    parser.add_argument('archive', help="path to gzipped archive with sessh binary")

    args = parser.parse_args()

    clone_homebrew_tap_repo()
    set_up_github_credentials()
    sha256_digest = generate_sha256_digest(args.archive)
    write_updated_brew_formula(args.version, sha256_digest)
    commit_and_push(args.version)
